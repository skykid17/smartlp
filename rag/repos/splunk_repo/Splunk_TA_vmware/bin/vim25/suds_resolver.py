import sys
from splunk.clilib.bundle_paths import make_splunkhome_path

sys.path.append(make_splunkhome_path(['etc', 'apps', 'Splunk_TA_vmware', 'bin', 'python3']))
import python3.suds as suds

sys.modules[__name__] = suds.__name__
