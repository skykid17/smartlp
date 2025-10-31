#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import json
import tempfile
import traceback
import boto3
import botocore
import solnlib

from typing import Optional
from time import time
from boto3.s3.transfer import TransferConfig

from requests import Response
from .logger_adapter import CSLoggerAdapter
from typing import Union, Dict, Any, List

KB = 1024
MB = 1024 * KB
DEFAULT_MAX_IN_MEM_SIZE = 30 * MB
DEFAULT_DOWNLOAD_CHUNK_SIZE = 2 * MB

logger = CSLoggerAdapter(
    solnlib.log.Logs().get_logger("splunk_ta_crowdstrike_fdr").getChild("aws_helpers")
)
boto3.compat.filter_python_deprecation_warnings()


class AwsOpsException(Exception):
    def __init__(self, err: Response, recoverable: bool = True) -> None:
        self.recoverable = recoverable
        super(AwsOpsException, self).__init__(err)

    def __str__(self):
        err_msg = super(AwsOpsException, self).__str__()
        if not self.recoverable:
            return f"(unrecoverable) {err_msg}"
        return err_msg


def aws_validate_credentials(aws_creds: Dict[str, Any]) -> bool:
    try:
        boto3.client("sts", **aws_creds).get_caller_identity()
    except (botocore.exceptions.ClientError, botocore.exceptions.ProxyConnectionError):
        return False
    except Exception as e:
        msg = f"aws_validate_credentials unexpected error: {e}"
        tb = " ---> ".join(traceback.format_exc().split("\n"))
        solnlib.log.log_configuration_error(logger, e, msg_before=f"{msg} {tb}")
        msg = "FDR AWS collection details validation failed, please check TA logs for details"
        raise Exception(msg) from e

    return True


def aws_handle_exception(
    e: Union[
        botocore.exceptions.ProxyConnectionError,
        botocore.exceptions.ClientError,
        Exception,
    ]
) -> str:
    if isinstance(e, botocore.exceptions.ProxyConnectionError):
        msg = "<<< aws_error_message='Proxy connection error'"
        solnlib.log.log_connection_error(logger, e, msg_before=msg)
        # returning error message to re-raise exception outside upper layer 'except' block
        # to prevent dumping proxy credentials in exceptions traceback chain
        return msg

    if isinstance(e, botocore.exceptions.ClientError):
        error = e.response["Error"]
        solnlib.log.log_exception(
            logger,
            e,
            "AWS Error",
            msg_before=f"<<< aws_error_code={error['Code']}, aws_error_message='{error['Message']}'",
        )
        recovarable = e.response.get("Error", {}).get("Code") != "404"
        raise AwsOpsException(e, recovarable) from e

    msg = f"aws_error_message='{e}'"
    tb = " ---> ".join(traceback.format_exc().split("\n"))
    solnlib.log.log_exception(
        logger,
        e,
        "AWS Error",
        msg_before=f"{msg} {tb}",
    )

    raise AwsOpsException(e) from e


def aws_check_success(
    s3_config: Dict[str, Any], bucket: str, prefix: str
) -> Optional[bool]:
    success = None
    tm_start = time()
    error_msg = None
    bucket_resource = f"{prefix}/_SUCCESS"
    try:
        logger.debug(
            f">>> check_success_bucket={bucket}, check_success_bucket_prefix={prefix}"
        )

        s3 = boto3.client("s3", **s3_config)
        s3.head_object(Bucket=bucket, Key=bucket_resource)
        success = True
    except botocore.exceptions.ClientError as e:
        err_code = e.response["Error"]["Code"]
        if err_code in ["NoSuchKey", "404"]:
            success = False
        else:
            error = e.response["Error"]
            solnlib.log.log_exception(
                logger,
                e,
                "AWS Error",
                msg_before=f"<<< aws_error_code={error['Code']}, aws_error_message='{error['Message']}', aws_bucket='{bucket}', aws_bucket_resource='{bucket_resource}'",
            )
            raise AwsOpsException(e) from e
    except Exception as e:
        error_msg = aws_handle_exception(e)

    if error_msg:
        raise AwsOpsException(error_msg)

    msg = "<<< check_success_time_taken={:.3f}, found_SUCCESS={}"
    logger.debug(msg.format(time() - tm_start, success))

    return success


def aws_map_s3_bucket(s3_config: Dict[str, Any], bucket: str, start_time: str) -> str:
    logger.info(f"FDR S3 bucket monitor, scan started with checkoint: {start_time}")

    count = 0
    max_time = start_time

    try:
        s3 = boto3.client("s3", **s3_config)
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            page_content = [c for c in page["Contents"]]
            for item in page_content:
                event_file = item["Key"]
                if event_file.endswith("/_SUCCESS") or event_file.endswith("/"):
                    continue

                lastModified = str(item["LastModified"])
                if start_time is not None and start_time >= lastModified:
                    continue

                if max_time is None or max_time < lastModified:
                    max_time = lastModified

                batch = "/".join(event_file.split("/")[:-1])
                event_source = f"s3://{bucket}/{event_file}"
                logger.info(
                    f'FDR S3 bucket monitor, new event file detected: fdr_scan_checkpoint="{start_time}", '
                    + f"fdr_bucket={bucket}, fdr_event_batch={batch}, fdr_event_file={event_file}, "
                    + f'fdr_event_source={event_source}, fdr_event_file_last_modified="{lastModified}", '
                    + f'fdr_event_file_size={item["Size"]}'
                )
                count += 1
    except Exception as e:
        solnlib.log.log_exception(
            logger,
            e,
            "FDR S3 Bucket Monitor Error",
            msg_before=f"FDR S3 bucket monitor, scan finished with error: {e}",
        )
        aws_handle_exception(e)
    else:
        logger.info(
            f"FDR S3 bucket monitor, scan finished with new checkoint: {max_time}, new event files detected: {count}"
        )
    return max_time


def aws_receive_sqs_messages(
    sqs_config: Dict[str, Any],
    sqs_url: str,
    visibility_timeout: str,
    max_number_of_messages: str,
) -> List[Dict[str, Any]]:
    messages = []
    tm_start = time()
    error_msg = None
    try:
        msg = ">>> sqs_visibility_timeout={}, max_number_of_sqs_messages={}"
        logger.debug(msg.format(visibility_timeout, max_number_of_messages))

        sqs = boto3.resource("sqs", **sqs_config).Queue(url=sqs_url)
        response = sqs.receive_messages(
            VisibilityTimeout=visibility_timeout,
            MaxNumberOfMessages=max_number_of_messages,
        )

        for msg in response:
            data = json.loads(msg.body)
            data["receipt_handle"] = msg.receipt_handle
            data["received"] = time()
            data["visibility_timeout"] = visibility_timeout
            messages.append(data)

        msg = "<<< receive_sqs_messages_time_taken={:.3f}, receive_sqs_message_count={}"
        logger.debug(msg.format(time() - tm_start, len(messages)))

    except Exception as e:
        error_msg = aws_handle_exception(e)

    if error_msg:
        raise AwsOpsException(error_msg)

    return messages


def aws_delete_sqs_message(
    sqs_config: Dict[str, Any], sqs_url: str, receipt_handle: str
) -> None:
    tm_start = time()
    msg = ">>> delete_sqs_message_queue={}, receipt_handle={}"
    logger.debug(msg.format(sqs_url, receipt_handle))
    error_msg = None
    try:
        boto3.client("sqs", **sqs_config).delete_message(
            QueueUrl=sqs_url, ReceiptHandle=receipt_handle
        )
    except Exception as e:
        error_msg = aws_handle_exception(e)

    if error_msg:
        raise AwsOpsException(error_msg)

    msg = "<<< delete_sqs_message_time_taken={:.3f}, delete_sqs_message_queue={}, receipt_handle={}"
    logger.debug(msg.format(time() - tm_start, sqs_url, receipt_handle))


def aws_download_file(
    s3_config: Dict[str, Any],
    bucket: str,
    file_path: str,
    download_chunksize: int = DEFAULT_DOWNLOAD_CHUNK_SIZE,
    max_in_mem_size: int = DEFAULT_MAX_IN_MEM_SIZE,
) -> Optional[tempfile.SpooledTemporaryFile]:
    file_obj = None
    tm_start = time()
    error_msg = None
    try:
        logger.debug(
            ">>> download_file_bucket={}, download_file_path={}".format(
                bucket, file_path
            )
        )
        file_obj = tempfile.SpooledTemporaryFile(max_size=max_in_mem_size, mode="w+b")
        # https://bugs.python.org/issue35112
        if not hasattr(file_obj, "seekable"):
            file_obj.seekable = lambda: True

        conf = TransferConfig(multipart_chunksize=download_chunksize)
        bucket = boto3.resource("s3", **s3_config).Bucket(bucket)
        bucket.download_fileobj(file_path, file_obj, Config=conf)
        file_obj.seek(0)
    except Exception as e:
        if file_obj:
            file_obj.close()
            file_obj = None

        error_msg = aws_handle_exception(e)

    if error_msg:
        raise AwsOpsException(error_msg)

    msg = "<<< download_file_time_taken={:.3f}, download_file_path={}"
    logger.debug(msg.format(time() - tm_start, file_path))

    return file_obj
