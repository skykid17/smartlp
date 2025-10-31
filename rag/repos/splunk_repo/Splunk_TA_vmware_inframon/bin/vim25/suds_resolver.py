import sys
from splunk.clilib.bundle_paths import make_splunkhome_path

if sys.version_info[0] == 2:
    sys.path.append(make_splunkhome_path(['etc', 'apps', 'Splunk_TA_vmware_inframon', 'bin', 'python2']))
    import python2.suds as suds
else:
    sys.path.append(make_splunkhome_path(['etc', 'apps', 'Splunk_TA_vmware_inframon', 'bin', 'python3']))
    import python3.suds as suds

sys.modules[__name__] = suds.__name__
