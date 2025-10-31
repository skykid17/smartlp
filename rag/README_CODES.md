### rag/download_fields.py
```bash
cat > "/opt/SmartSOC/web/rag/download_fields.py" <<"ENDMSG"
from bs4 import BeautifulSoup
import requests
import pandas as pd

def download_splunk_fields():
    url = "https://help.splunk.com/en/splunk-enterprise/common-information-model/6.0/introduction/overview-of-the-splunk-common-information-model"

    response = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    })
    
    if response.status_code != 200:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        exit(1)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all ul elements with class "list-unstyled"
    data_model_sections = soup.find_all('ul', {'class': "list-unstyled"})


    # List to store all links
    all_links = []


    # Extract all hrefs
    for ul in data_model_sections:
        links = ul.find_all('a')
        for link in links:
            href = link.get('href', '')
            if href and href not in all_links and href.startswith('/Documentation/CIM/'):
                all_links.append(href)

    if not all_links:
        print("No links found. Exiting.")
        exit(1)

    def scrape_cim_data(url):
        """
        Scrape CIM data from the given URL.
        
        Args:
            url (str): The URL of the CIM data page.
            
        Returns:
            list: A list of dictionaries containing the scraped CIM data.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')
            # Example of scraping logic; adjust according to actual HTML structure
            cim_data_list = []
            
            # Find all tables on the page (there might be multiple)
            tables = soup.find_all('table')
            
            for table_index, table in enumerate(tables):
                # Get headers to check the number of columns
                headers = [header.text.strip() for header in table.find_all('th')]
                
                # Skip tables that don't have exactly 5 columns
                if len(headers) != 5:
                    print(f"Table {table_index + 1}: Found {len(headers)} columns, expected 5. Skipping table.")
                    continue
                    
                print(f"Table {table_index + 1}: Processing table with 5 columns: {headers}")
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) != 5:  # Only process rows with exactly 5 cells
                        continue
                    
                    row_data = {
                        "Dataset_name": cells[0].text.strip(),
                        "Field_name": cells[1].text.strip(),
                        "Data_type": cells[2].text.strip(),
                        "Description": cells[3].text.strip(),
                        "Notes": cells[4].text.strip()  # Always save as "Notes" regardless of original column name
                    }
                    cim_data_list.append(row_data)
            
            return cim_data_list
        
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return []
        except Exception as e:
            print(f"Error parsing data from {url}: {e}")
            return []

    all_cim_data = []

    for link in sorted(all_links):
        cim_data = scrape_cim_data(f"https://docs.splunk.com{link}")
        print(f"Scraped {len(cim_data)} records from https://docs.splunk.com{link}")
        all_cim_data.extend(cim_data)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(all_cim_data)
    # Save the DataFrame to a CSV file
    df.to_csv("./rag/splunk_fields.csv", index=False)
    print(f"CIM data scraped and saved to splunk_fields.csv ({len(all_cim_data)} records)")

def download_elastic_fields():
    """
    Download the fields CSV file from the Elastic GitHub repository.
    """
    headers = {
    "Accept": "application/vnd.github.v3.raw"  # Get the raw file content
    }  

    try:
        response = requests.get("https://raw.githubusercontent.com/elastic/ecs/master/generated/csv/fields.csv", headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        with open("./rag/elastic_fields.csv", "wb") as file:
            file.write(response.content)
        print("Downloaded elastic_fields.csv successfully.")
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")
    # Set the repo and file path

#download_splunk_fields()

#download_elastic_fields()ENDMSG
```
---
### rag/elastic_fields.csv
```bash
cat > "/opt/SmartSOC/web/rag/elastic_fields.csv" <<"ENDMSG"
ECS_Version,Indexed,Field_Set,Field,Type,Level,Normalization,Example,Description
9.2.0-dev,true,base,@timestamp,date,core,,2016-05-23T08:05:34.853Z,Date/time when the event originated.
9.2.0-dev,true,base,labels,object,core,,"{""application"": ""foo-bar"", ""env"": ""production""}",Custom key/value pairs.
9.2.0-dev,true,base,message,match_only_text,core,,Hello World,Log message optimized for viewing in a log viewer.
9.2.0-dev,true,base,tags,keyword,core,array,"[""production"", ""env2""]",List of keywords used to tag each event.
9.2.0-dev,true,agent,agent.build.original,keyword,core,,"metricbeat version 7.6.0 (amd64), libbeat 7.6.0 [6a23e8f8f30f5001ba344e4e54d8d9cb82cb107c built 2020-02-05 23:10:10 +0000 UTC]",Extended build information for the agent.
9.2.0-dev,true,agent,agent.ephemeral_id,keyword,extended,,8a4f500f,Ephemeral identifier of this agent.
9.2.0-dev,true,agent,agent.id,keyword,core,,8a4f500d,Unique identifier of this agent.
9.2.0-dev,true,agent,agent.name,keyword,core,,foo,Custom name of the agent.
9.2.0-dev,true,agent,agent.type,keyword,core,,filebeat,Type of the agent.
9.2.0-dev,true,agent,agent.version,keyword,core,,6.0.0-rc2,Version of the agent.
9.2.0-dev,true,client,client.address,keyword,extended,,,Client network address.
9.2.0-dev,true,client,client.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,client,client.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,client,client.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,client,client.bytes,long,core,,184,Bytes sent from the client to the server.
9.2.0-dev,true,client,client.domain,keyword,core,,foo.example.com,The domain name of the client.
9.2.0-dev,true,client,client.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,client,client.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,client,client.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,client,client.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,client,client.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,client,client.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,client,client.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,client,client.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,client,client.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,client,client.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,client,client.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,client,client.ip,ip,core,,,IP address of the client.
9.2.0-dev,true,client,client.mac,keyword,core,,00-00-5E-00-53-23,MAC address of the client.
9.2.0-dev,true,client,client.nat.ip,ip,extended,,,Client NAT ip address
9.2.0-dev,true,client,client.nat.port,long,extended,,,Client NAT port
9.2.0-dev,true,client,client.packets,long,core,,12,Packets sent from the client to the server.
9.2.0-dev,true,client,client.port,long,core,,,Port of the client.
9.2.0-dev,true,client,client.registered_domain,keyword,extended,,example.com,"The highest registered client domain, stripped of the subdomain."
9.2.0-dev,true,client,client.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,client,client.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,client,client.user.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,client,client.user.email,keyword,extended,,,User email address.
9.2.0-dev,true,client,client.user.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,client,client.user.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,client,client.user.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,client,client.user.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,client,client.user.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,client,client.user.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,client,client.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,client,client.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,client,client.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,client,client.user.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,cloud,cloud.account.id,keyword,extended,,666777888999,The cloud account or organization id.
9.2.0-dev,true,cloud,cloud.account.name,keyword,extended,,elastic-dev,The cloud account name.
9.2.0-dev,true,cloud,cloud.availability_zone,keyword,extended,,us-east-1c,"Availability zone in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.instance.id,keyword,extended,,i-1234567890abcdef0,Instance ID of the host machine.
9.2.0-dev,true,cloud,cloud.instance.name,keyword,extended,,,Instance name of the host machine.
9.2.0-dev,true,cloud,cloud.machine.type,keyword,extended,,t2.medium,Machine type of the host machine.
9.2.0-dev,true,cloud,cloud.origin.account.id,keyword,extended,,666777888999,The cloud account or organization id.
9.2.0-dev,true,cloud,cloud.origin.account.name,keyword,extended,,elastic-dev,The cloud account name.
9.2.0-dev,true,cloud,cloud.origin.availability_zone,keyword,extended,,us-east-1c,"Availability zone in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.origin.instance.id,keyword,extended,,i-1234567890abcdef0,Instance ID of the host machine.
9.2.0-dev,true,cloud,cloud.origin.instance.name,keyword,extended,,,Instance name of the host machine.
9.2.0-dev,true,cloud,cloud.origin.machine.type,keyword,extended,,t2.medium,Machine type of the host machine.
9.2.0-dev,true,cloud,cloud.origin.project.id,keyword,extended,,my-project,The cloud project id.
9.2.0-dev,true,cloud,cloud.origin.project.name,keyword,extended,,my project,The cloud project name.
9.2.0-dev,true,cloud,cloud.origin.provider,keyword,extended,,aws,Name of the cloud provider.
9.2.0-dev,true,cloud,cloud.origin.region,keyword,extended,,us-east-1,"Region in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.origin.service.name,keyword,extended,,lambda,The cloud service name.
9.2.0-dev,true,cloud,cloud.project.id,keyword,extended,,my-project,The cloud project id.
9.2.0-dev,true,cloud,cloud.project.name,keyword,extended,,my project,The cloud project name.
9.2.0-dev,true,cloud,cloud.provider,keyword,extended,,aws,Name of the cloud provider.
9.2.0-dev,true,cloud,cloud.region,keyword,extended,,us-east-1,"Region in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.service.name,keyword,extended,,lambda,The cloud service name.
9.2.0-dev,true,cloud,cloud.target.account.id,keyword,extended,,666777888999,The cloud account or organization id.
9.2.0-dev,true,cloud,cloud.target.account.name,keyword,extended,,elastic-dev,The cloud account name.
9.2.0-dev,true,cloud,cloud.target.availability_zone,keyword,extended,,us-east-1c,"Availability zone in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.target.instance.id,keyword,extended,,i-1234567890abcdef0,Instance ID of the host machine.
9.2.0-dev,true,cloud,cloud.target.instance.name,keyword,extended,,,Instance name of the host machine.
9.2.0-dev,true,cloud,cloud.target.machine.type,keyword,extended,,t2.medium,Machine type of the host machine.
9.2.0-dev,true,cloud,cloud.target.project.id,keyword,extended,,my-project,The cloud project id.
9.2.0-dev,true,cloud,cloud.target.project.name,keyword,extended,,my project,The cloud project name.
9.2.0-dev,true,cloud,cloud.target.provider,keyword,extended,,aws,Name of the cloud provider.
9.2.0-dev,true,cloud,cloud.target.region,keyword,extended,,us-east-1,"Region in which this host, resource, or service is located."
9.2.0-dev,true,cloud,cloud.target.service.name,keyword,extended,,lambda,The cloud service name.
9.2.0-dev,true,container,container.cpu.usage,scaled_float,extended,,,"Percent CPU used, between 0 and 1."
9.2.0-dev,true,container,container.disk.read.bytes,long,extended,,,The number of bytes read by all disks.
9.2.0-dev,true,container,container.disk.write.bytes,long,extended,,,The number of bytes written on all disks.
9.2.0-dev,true,container,container.id,keyword,core,,,Unique container id.
9.2.0-dev,true,container,container.image.hash.all,keyword,extended,array,[sha256:f8fefc80e3273dc756f288a63945820d6476ad64883892c771b5e2ece6bf1b26],An array of digests of the image the container was built on.
9.2.0-dev,true,container,container.image.name,keyword,extended,,,Name of the image the container was built on.
9.2.0-dev,true,container,container.image.tag,keyword,extended,array,,Container image tags.
9.2.0-dev,true,container,container.labels,object,extended,,,Image labels.
9.2.0-dev,true,container,container.memory.usage,scaled_float,extended,,,"Percent memory used, between 0 and 1."
9.2.0-dev,true,container,container.name,keyword,extended,,,Container name.
9.2.0-dev,true,container,container.network.egress.bytes,long,extended,,,The number of bytes sent on all network interfaces.
9.2.0-dev,true,container,container.network.ingress.bytes,long,extended,,,The number of bytes received on all network interfaces.
9.2.0-dev,true,container,container.runtime,keyword,extended,,docker,Runtime managing this container.
9.2.0-dev,true,container,container.security_context.privileged,boolean,extended,,,Indicates whether the container is running in privileged mode.
9.2.0-dev,true,data_stream,data_stream.dataset,constant_keyword,extended,,nginx.access,The field can contain anything that makes sense to signify the source of the data.
9.2.0-dev,true,data_stream,data_stream.namespace,constant_keyword,extended,,production,A user defined namespace. Namespaces are useful to allow grouping of data.
9.2.0-dev,true,data_stream,data_stream.type,constant_keyword,extended,,logs,An overarching type for the data stream.
9.2.0-dev,true,destination,destination.address,keyword,extended,,,Destination network address.
9.2.0-dev,true,destination,destination.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,destination,destination.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,destination,destination.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,destination,destination.bytes,long,core,,184,Bytes sent from the destination to the source.
9.2.0-dev,true,destination,destination.domain,keyword,core,,foo.example.com,The domain name of the destination.
9.2.0-dev,true,destination,destination.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,destination,destination.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,destination,destination.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,destination,destination.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,destination,destination.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,destination,destination.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,destination,destination.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,destination,destination.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,destination,destination.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,destination,destination.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,destination,destination.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,destination,destination.ip,ip,core,,,IP address of the destination.
9.2.0-dev,true,destination,destination.mac,keyword,core,,00-00-5E-00-53-23,MAC address of the destination.
9.2.0-dev,true,destination,destination.nat.ip,ip,extended,,,Destination NAT ip
9.2.0-dev,true,destination,destination.nat.port,long,extended,,,Destination NAT Port
9.2.0-dev,true,destination,destination.packets,long,core,,12,Packets sent from the destination to the source.
9.2.0-dev,true,destination,destination.port,long,core,,,Port of the destination.
9.2.0-dev,true,destination,destination.registered_domain,keyword,extended,,example.com,"The highest registered destination domain, stripped of the subdomain."
9.2.0-dev,true,destination,destination.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,destination,destination.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,destination,destination.user.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,destination,destination.user.email,keyword,extended,,,User email address.
9.2.0-dev,true,destination,destination.user.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,destination,destination.user.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,destination,destination.user.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,destination,destination.user.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,destination,destination.user.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,destination,destination.user.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,destination,destination.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,destination,destination.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,destination,destination.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,destination,destination.user.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,device,device.id,keyword,extended,,00000000-54b3-e7c7-0000-000046bffd97,The unique identifier of a device.
9.2.0-dev,true,device,device.manufacturer,keyword,extended,,Samsung,The vendor name of the device manufacturer.
9.2.0-dev,true,device,device.model.identifier,keyword,extended,,SM-G920F,The machine readable identifier of the device model.
9.2.0-dev,true,device,device.model.name,keyword,extended,,Samsung Galaxy S6,The human readable marketing name of the device model.
9.2.0-dev,true,device,device.serial_number,keyword,core,,DJGAQS4CW5,Serial Number of the device
9.2.0-dev,true,dll,dll.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,dll,dll.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,dll,dll.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,dll,dll.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,dll,dll.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,dll,dll.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,dll,dll.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,dll,dll.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,dll,dll.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,dll,dll.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,dll,dll.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,dll,dll.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,dll,dll.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,dll,dll.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,dll,dll.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,dll,dll.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,dll,dll.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,dll,dll.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,dll,dll.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,dll,dll.name,keyword,core,,kernel32.dll,Name of the library.
9.2.0-dev,true,dll,dll.origin_referrer_url,keyword,extended,,http://example.com/article1.html,The URL of the webpage that linked to the dll file.
9.2.0-dev,true,dll,dll.origin_url,keyword,extended,,http://example.com/files/example.dll,The URL where the dll file is hosted.
9.2.0-dev,true,dll,dll.path,keyword,extended,,C:\Windows\System32\kernel32.dll,Full file path of the library.
9.2.0-dev,true,dll,dll.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,dll,dll.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,dll,dll.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,dll,dll.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,dll,dll.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,dll,dll.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,dll,dll.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,dll,dll.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,dll,dll.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,dll,dll.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,dll,dll.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,dll,dll.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,dll,dll.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,dll,dll.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,dll,dll.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,dll,dll.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,dll,dll.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,dll,dll.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,dll,dll.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,dll,dll.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,dll,dll.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,dll,dll.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,dll,dll.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,dns,dns.answers,object,extended,array,,Array of DNS answers.
9.2.0-dev,true,dns,dns.answers.class,keyword,extended,,IN,The class of DNS data contained in this resource record.
9.2.0-dev,true,dns,dns.answers.data,keyword,extended,,10.10.10.10,The data describing the resource.
9.2.0-dev,true,dns,dns.answers.name,keyword,extended,,www.example.com,The domain name to which this resource record pertains.
9.2.0-dev,true,dns,dns.answers.ttl,long,extended,,180,The time interval in seconds that this resource record may be cached before it should be discarded.
9.2.0-dev,true,dns,dns.answers.type,keyword,extended,,CNAME,The type of data contained in this resource record.
9.2.0-dev,true,dns,dns.header_flags,keyword,extended,array,"[""RD"", ""RA""]",Array of DNS header flags.
9.2.0-dev,true,dns,dns.id,keyword,extended,,62111,The DNS packet identifier assigned by the program that generated the query. The identifier is copied to the response.
9.2.0-dev,true,dns,dns.op_code,keyword,extended,,QUERY,The DNS operation code that specifies the kind of query in the message.
9.2.0-dev,true,dns,dns.question.class,keyword,extended,,IN,The class of records being queried.
9.2.0-dev,true,dns,dns.question.name,keyword,extended,,www.example.com,The name being queried.
9.2.0-dev,true,dns,dns.question.registered_domain,keyword,extended,,example.com,"The highest registered domain, stripped of the subdomain."
9.2.0-dev,true,dns,dns.question.subdomain,keyword,extended,,www,The subdomain of the domain.
9.2.0-dev,true,dns,dns.question.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,dns,dns.question.type,keyword,extended,,AAAA,The type of record being queried.
9.2.0-dev,true,dns,dns.resolved_ip,ip,extended,array,"[""10.10.10.10"", ""10.10.10.11""]",Array containing all IPs seen in answers.data
9.2.0-dev,true,dns,dns.response_code,keyword,extended,,NOERROR,The DNS response code.
9.2.0-dev,true,dns,dns.type,keyword,extended,,answer,"The type of DNS event captured, query or answer."
9.2.0-dev,true,ecs,ecs.version,keyword,core,,1.0.0,ECS version this event conforms to.
9.2.0-dev,true,email,email.attachments,nested,extended,array,,List of objects describing the attachments.
9.2.0-dev,true,email,email.attachments.file.extension,keyword,extended,,txt,Attachment file extension.
9.2.0-dev,true,email,email.attachments.file.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,email,email.attachments.file.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,email,email.attachments.file.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,email,email.attachments.file.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,email,email.attachments.file.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,email,email.attachments.file.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,email,email.attachments.file.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,email,email.attachments.file.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,email,email.attachments.file.mime_type,keyword,extended,,text/plain,MIME type of the attachment file.
9.2.0-dev,true,email,email.attachments.file.name,keyword,extended,,attachment.txt,Name of the attachment file.
9.2.0-dev,true,email,email.attachments.file.size,long,extended,,64329,Attachment file size.
9.2.0-dev,true,email,email.bcc.address,keyword,extended,array,bcc.user1@example.com,Email address of BCC recipient
9.2.0-dev,true,email,email.cc.address,keyword,extended,array,cc.user1@example.com,Email address of CC recipient
9.2.0-dev,true,email,email.content_type,keyword,extended,,text/plain,MIME type of the email message.
9.2.0-dev,true,email,email.delivery_timestamp,date,extended,,2020-11-10T22:12:34.8196921Z,Date and time when message was delivered.
9.2.0-dev,true,email,email.direction,keyword,extended,,inbound,Direction of the message.
9.2.0-dev,true,email,email.from.address,keyword,extended,array,sender@example.com,The sender's email address.
9.2.0-dev,true,email,email.local_id,keyword,extended,,c26dbea0-80d5-463b-b93c-4e8b708219ce,Unique identifier given by the source.
9.2.0-dev,true,email,email.message_id,wildcard,extended,,81ce15$8r2j59@mail01.example.com,Value from the Message-ID header.
9.2.0-dev,true,email,email.origination_timestamp,date,extended,,2020-11-10T22:12:34.8196921Z,Date and time the email was composed.
9.2.0-dev,true,email,email.reply_to.address,keyword,extended,array,reply.here@example.com,Address replies should be delivered to.
9.2.0-dev,true,email,email.sender.address,keyword,extended,,,Address of the message sender.
9.2.0-dev,true,email,email.subject,keyword,extended,,Please see this important message.,The subject of the email message.
9.2.0-dev,true,email,email.subject.text,match_only_text,extended,,Please see this important message.,The subject of the email message.
9.2.0-dev,true,email,email.to.address,keyword,extended,array,user1@example.com,Email address of recipient
9.2.0-dev,true,email,email.x_mailer,keyword,extended,,Spambot v2.5,Application that drafted email.
9.2.0-dev,true,error,error.code,keyword,core,,,Error code describing the error.
9.2.0-dev,true,error,error.id,keyword,core,,,Unique identifier for the error.
9.2.0-dev,true,error,error.message,match_only_text,core,,,Error message.
9.2.0-dev,true,error,error.stack_trace,wildcard,extended,,,The stack trace of this error in plain text.
9.2.0-dev,true,error,error.stack_trace.text,match_only_text,extended,,,The stack trace of this error in plain text.
9.2.0-dev,true,error,error.type,keyword,extended,,java.lang.NullPointerException,"The type of the error, for example the class name of the exception."
9.2.0-dev,true,event,event.action,keyword,core,,user-password-change,The action captured by the event.
9.2.0-dev,true,event,event.agent_id_status,keyword,extended,,verified,Validation status of the event's agent.id field.
9.2.0-dev,true,event,event.category,keyword,core,array,authentication,Event category. The second categorization field in the hierarchy.
9.2.0-dev,true,event,event.code,keyword,extended,,4648,Identification code for this event.
9.2.0-dev,true,event,event.created,date,core,,2016-05-23T08:05:34.857Z,Time when the event was first read by an agent or by your pipeline.
9.2.0-dev,true,event,event.dataset,keyword,core,,apache.access,Name of the dataset.
9.2.0-dev,true,event,event.duration,long,core,,,Duration of the event in nanoseconds.
9.2.0-dev,true,event,event.end,date,extended,,,`event.end` contains the date when the event ended or when the activity was last observed.
9.2.0-dev,true,event,event.hash,keyword,extended,,123456789012345678901234567890ABCD,Hash (perhaps logstash fingerprint) of raw field to be able to demonstrate log integrity.
9.2.0-dev,true,event,event.id,keyword,core,,8a4f500d,Unique ID to describe the event.
9.2.0-dev,true,event,event.ingested,date,core,,2016-05-23T08:05:35.101Z,Timestamp when an event arrived in the central data store.
9.2.0-dev,true,event,event.kind,keyword,core,,alert,The kind of the event. The highest categorization field in the hierarchy.
9.2.0-dev,true,event,event.module,keyword,core,,apache,Name of the module this data is coming from.
9.2.0-dev,false,event,event.original,keyword,core,,Sep 19 08:26:10 host CEF:0&#124;Security&#124; threatmanager&#124;1.0&#124;100&#124; worm successfully stopped&#124;10&#124;src=10.0.0.1 dst=2.1.2.2spt=1232,Raw text message of entire event.
9.2.0-dev,true,event,event.outcome,keyword,core,,success,The outcome of the event. The lowest level categorization field in the hierarchy.
9.2.0-dev,true,event,event.provider,keyword,extended,,kernel,Source of the event.
9.2.0-dev,true,event,event.reason,keyword,extended,,Terminated an unexpected process,"Reason why this event happened, according to the source"
9.2.0-dev,true,event,event.reference,keyword,extended,,https://system.example.com/event/#0001234,Event reference URL
9.2.0-dev,true,event,event.risk_score,float,core,,,Risk score or priority of the event (e.g. security solutions). Use your system's original value here.
9.2.0-dev,true,event,event.risk_score_norm,float,extended,,,Normalized risk score or priority of the event (0-100).
9.2.0-dev,true,event,event.sequence,long,extended,,,Sequence number of the event.
9.2.0-dev,true,event,event.severity,long,core,,7,Numeric severity of the event.
9.2.0-dev,true,event,event.start,date,extended,,,`event.start` contains the date when the event started or when the activity was first observed.
9.2.0-dev,true,event,event.timezone,keyword,extended,,,Event time zone.
9.2.0-dev,true,event,event.type,keyword,core,array,,Event type. The third categorization field in the hierarchy.
9.2.0-dev,true,event,event.url,keyword,extended,,https://mysystem.example.com/alert/5271dedb-f5b0-4218-87f0-4ac4870a38fe,Event investigation URL
9.2.0-dev,true,faas,faas.coldstart,boolean,extended,,,Boolean value indicating a cold start of a function.
9.2.0-dev,true,faas,faas.execution,keyword,extended,,af9d5aa4-a685-4c5f-a22b-444f80b3cc28,The execution ID of the current function execution.
9.2.0-dev,true,faas,faas.id,keyword,extended,,arn:aws:lambda:us-west-2:123456789012:function:my-function,The unique identifier of a serverless function.
9.2.0-dev,true,faas,faas.name,keyword,extended,,my-function,The name of a serverless function.
9.2.0-dev,true,faas,faas.trigger.request_id,keyword,extended,,123456789,"The ID of the trigger request , message, event, etc."
9.2.0-dev,true,faas,faas.trigger.type,keyword,extended,,http,The trigger for the function execution.
9.2.0-dev,true,faas,faas.version,keyword,extended,,123,The version of a serverless function.
9.2.0-dev,true,file,file.accessed,date,extended,,,Last time the file was accessed.
9.2.0-dev,true,file,file.attributes,keyword,extended,array,"[""readonly"", ""system""]",Array of file attributes.
9.2.0-dev,true,file,file.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,file,file.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,file,file.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,file,file.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,file,file.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,file,file.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,file,file.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,file,file.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,file,file.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,file,file.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,file,file.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,file,file.created,date,extended,,,File creation time.
9.2.0-dev,true,file,file.ctime,date,extended,,,Last time the file attributes or metadata changed.
9.2.0-dev,true,file,file.device,keyword,extended,,sda,Device that is the source of the file.
9.2.0-dev,true,file,file.directory,keyword,extended,,/home/alice,Directory where the file is located.
9.2.0-dev,true,file,file.drive_letter,keyword,extended,,C,Drive letter where the file is located.
9.2.0-dev,true,file,file.elf.architecture,keyword,extended,,x86-64,Machine architecture of the ELF file.
9.2.0-dev,true,file,file.elf.byte_order,keyword,extended,,Little Endian,Byte sequence of ELF file.
9.2.0-dev,true,file,file.elf.cpu_type,keyword,extended,,Intel,CPU type of the ELF file.
9.2.0-dev,true,file,file.elf.creation_date,date,extended,,,Build or compile date.
9.2.0-dev,true,file,file.elf.exports,flattened,extended,array,,List of exported element names and types.
9.2.0-dev,true,file,file.elf.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in an ELF file.
9.2.0-dev,true,file,file.elf.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,file,file.elf.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.elf.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.elf.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,file,file.elf.header.abi_version,keyword,extended,,,Version of the ELF Application Binary Interface (ABI).
9.2.0-dev,true,file,file.elf.header.class,keyword,extended,,,Header class of the ELF file.
9.2.0-dev,true,file,file.elf.header.data,keyword,extended,,,Data table of the ELF header.
9.2.0-dev,true,file,file.elf.header.entrypoint,long,extended,,,Header entrypoint of the ELF file.
9.2.0-dev,true,file,file.elf.header.object_version,keyword,extended,,,"""0x1"" for original ELF files."
9.2.0-dev,true,file,file.elf.header.os_abi,keyword,extended,,,Application Binary Interface (ABI) of the Linux OS.
9.2.0-dev,true,file,file.elf.header.type,keyword,extended,,,Header type of the ELF file.
9.2.0-dev,true,file,file.elf.header.version,keyword,extended,,,Version of the ELF header.
9.2.0-dev,true,file,file.elf.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in an ELF file.
9.2.0-dev,true,file,file.elf.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,file,file.elf.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.elf.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.elf.sections,nested,extended,array,,Section information of the ELF file.
9.2.0-dev,true,file,file.elf.sections.chi2,long,extended,,,Chi-square probability distribution of the section.
9.2.0-dev,true,file,file.elf.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.elf.sections.flags,keyword,extended,,,ELF Section List flags.
9.2.0-dev,true,file,file.elf.sections.name,keyword,extended,,,ELF Section List name.
9.2.0-dev,true,file,file.elf.sections.physical_offset,keyword,extended,,,ELF Section List offset.
9.2.0-dev,true,file,file.elf.sections.physical_size,long,extended,,,ELF Section List physical size.
9.2.0-dev,true,file,file.elf.sections.type,keyword,extended,,,ELF Section List type.
9.2.0-dev,true,file,file.elf.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.elf.sections.virtual_address,long,extended,,,ELF Section List virtual address.
9.2.0-dev,true,file,file.elf.sections.virtual_size,long,extended,,,ELF Section List virtual size.
9.2.0-dev,true,file,file.elf.segments,nested,extended,array,,ELF object segment list.
9.2.0-dev,true,file,file.elf.segments.sections,keyword,extended,,,ELF object segment sections.
9.2.0-dev,true,file,file.elf.segments.type,keyword,extended,,,ELF object segment type.
9.2.0-dev,true,file,file.elf.shared_libraries,keyword,extended,array,,List of shared libraries used by this ELF object.
9.2.0-dev,true,file,file.elf.telfhash,keyword,extended,,,telfhash hash for ELF file.
9.2.0-dev,true,file,file.extension,keyword,extended,,png,"File extension, excluding the leading dot."
9.2.0-dev,true,file,file.fork_name,keyword,extended,,Zone.Identifer,A fork is additional data associated with a filesystem object.
9.2.0-dev,true,file,file.gid,keyword,extended,,1001,Primary group ID (GID) of the file.
9.2.0-dev,true,file,file.group,keyword,extended,,alice,Primary group name of the file.
9.2.0-dev,true,file,file.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,file,file.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,file,file.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,file,file.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,file,file.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,file,file.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,file,file.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,file,file.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,file,file.inode,keyword,extended,,256383,Inode representing the file in the filesystem.
9.2.0-dev,true,file,file.macho.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a Mach-O file.
9.2.0-dev,true,file,file.macho.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,file,file.macho.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.macho.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.macho.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,file,file.macho.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a Mach-O file.
9.2.0-dev,true,file,file.macho.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,file,file.macho.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.macho.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.macho.sections,nested,extended,array,,Section information of the Mach-O file.
9.2.0-dev,true,file,file.macho.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.macho.sections.name,keyword,extended,,,Mach-O Section List name.
9.2.0-dev,true,file,file.macho.sections.physical_size,long,extended,,,Mach-O Section List physical size.
9.2.0-dev,true,file,file.macho.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.macho.sections.virtual_size,long,extended,,,Mach-O Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,file,file.macho.symhash,keyword,extended,,d3ccf195b62a9279c3c19af1080497ec,A hash of the imports in a Mach-O file.
9.2.0-dev,true,file,file.mime_type,keyword,extended,,,"Media type of file, document, or arrangement of bytes."
9.2.0-dev,true,file,file.mode,keyword,extended,,0640,Mode of the file in octal representation.
9.2.0-dev,true,file,file.mtime,date,extended,,,Last time the file content was modified.
9.2.0-dev,true,file,file.name,keyword,extended,,example.png,"Name of the file including the extension, without the directory."
9.2.0-dev,true,file,file.origin_referrer_url,keyword,extended,,http://example.com/article1.html,The URL of the webpage that linked to the file.
9.2.0-dev,true,file,file.origin_url,keyword,extended,,http://example.com/imgs/article1_img1.jpg,The URL where the file is hosted.
9.2.0-dev,true,file,file.owner,keyword,extended,,alice,File owner's username.
9.2.0-dev,true,file,file.path,keyword,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,file,file.path.text,match_only_text,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,file,file.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,file,file.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,file,file.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,file,file.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,file,file.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,file,file.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,file,file.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,file,file.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,file,file.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,file,file.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,file,file.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,file,file.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,file,file.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,file,file.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,file,file.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,file,file.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,file,file.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,file,file.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,file,file.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,file,file.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,file,file.size,long,extended,,16384,File size in bytes.
9.2.0-dev,true,file,file.target_path,keyword,extended,,,Target path for symlinks.
9.2.0-dev,true,file,file.target_path.text,match_only_text,extended,,,Target path for symlinks.
9.2.0-dev,true,file,file.type,keyword,extended,,file,"File type (file, dir, or symlink)."
9.2.0-dev,true,file,file.uid,keyword,extended,,1001,The user ID (UID) or security identifier (SID) of the file owner.
9.2.0-dev,true,file,file.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,file,file.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,file,file.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,file,file.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,file,file.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,file,file.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,file,file.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,file,file.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,file,file.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,file,file.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,file,file.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,file,file.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,file,file.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,file,file.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,file,file.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,file,file.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,file,file.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,file,file.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,file,file.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,file,file.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,file,file.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,file,file.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,file,file.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,file,file.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,false,gen_ai,gen_ai.agent.description,keyword,extended,,Helps with math problems; Generates fiction stories,Free-form description of the GenAI agent provided by the application.
9.2.0-dev,true,gen_ai,gen_ai.agent.id,keyword,extended,,asst_5j66UpCpwteGg4YSxUnt7lPY,The unique identifier of the GenAI agent.
9.2.0-dev,true,gen_ai,gen_ai.agent.name,keyword,extended,,Math Tutor; Fiction Writer,Human-readable name of the GenAI agent provided by the application.
9.2.0-dev,true,gen_ai,gen_ai.operation.name,keyword,extended,,chat; text_completion; embeddings,The name of the operation being performed.
9.2.0-dev,true,gen_ai,gen_ai.output.type,keyword,extended,,text; json; image,Represents the content type requested by the client.
9.2.0-dev,true,gen_ai,gen_ai.request.choice.count,integer,extended,,3,The target number of candidate completions to return.
9.2.0-dev,true,gen_ai,gen_ai.request.encoding_formats,nested,extended,,"[""float"", ""binary""]","The encoding formats requested in an embeddings operation, if specified."
9.2.0-dev,true,gen_ai,gen_ai.request.frequency_penalty,double,extended,,0.1,The frequency penalty setting for the GenAI request.
9.2.0-dev,true,gen_ai,gen_ai.request.max_tokens,integer,extended,,100,The maximum number of tokens the model generates for a request.
9.2.0-dev,true,gen_ai,gen_ai.request.model,keyword,extended,,gpt-4,The name of the GenAI model a request is being made to.
9.2.0-dev,true,gen_ai,gen_ai.request.presence_penalty,double,extended,,0.1,The presence penalty setting for the GenAI request.
9.2.0-dev,true,gen_ai,gen_ai.request.seed,integer,extended,,100,Requests with same seed value more likely to return same result.
9.2.0-dev,true,gen_ai,gen_ai.request.stop_sequences,nested,extended,,"[""forest"", ""lived""]",List of sequences that the model will use to stop generating further tokens.
9.2.0-dev,true,gen_ai,gen_ai.request.temperature,double,extended,,0.0,The temperature setting for the GenAI request.
9.2.0-dev,true,gen_ai,gen_ai.request.top_k,double,extended,,1.0,The top_k sampling setting for the GenAI request.
9.2.0-dev,true,gen_ai,gen_ai.request.top_p,double,extended,,1.0,The top_p sampling setting for the GenAI request.
9.2.0-dev,true,gen_ai,gen_ai.response.finish_reasons,nested,extended,,"[""stop"", ""length""]","Array of reasons the model stopped generating tokens, corresponding to each generation received."
9.2.0-dev,true,gen_ai,gen_ai.response.id,keyword,extended,,chatcmpl-123,The unique identifier for the completion.
9.2.0-dev,true,gen_ai,gen_ai.response.model,keyword,extended,,gpt-4-0613,The name of the model that generated the response.
9.2.0-dev,true,gen_ai,gen_ai.system,keyword,extended,,openai,The Generative AI product as identified by the client or server instrumentation.
9.2.0-dev,true,gen_ai,gen_ai.token.type,keyword,extended,,input; output,The type of token being counted.
9.2.0-dev,true,gen_ai,gen_ai.tool.call.id,keyword,extended,,call_mszuSIzqtI65i1wAUOE8w5H4,The tool call identifier.
9.2.0-dev,true,gen_ai,gen_ai.tool.name,keyword,extended,,Flights,Name of the tool utilized by the agent.
9.2.0-dev,true,gen_ai,gen_ai.tool.type,keyword,extended,,function; extension; datastore,Type of the tool utilized by the agent
9.2.0-dev,true,gen_ai,gen_ai.usage.input_tokens,integer,extended,,100,The number of tokens used in the GenAI input (prompt).
9.2.0-dev,true,gen_ai,gen_ai.usage.output_tokens,integer,extended,,180,The number of tokens used in the GenAI response (completion).
9.2.0-dev,true,group,group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,group,group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,group,group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,host,host.architecture,keyword,core,,x86_64,Operating system architecture.
9.2.0-dev,true,host,host.boot.id,keyword,extended,,88a1f0ed-5ae5-41ee-af6b-41921c311872,Linux boot uuid taken from /proc/sys/kernel/random/boot_id
9.2.0-dev,true,host,host.cpu.usage,scaled_float,extended,,,"Percent CPU used, between 0 and 1."
9.2.0-dev,true,host,host.disk.read.bytes,long,extended,,,The number of bytes read by all disks.
9.2.0-dev,true,host,host.disk.write.bytes,long,extended,,,The number of bytes written on all disks.
9.2.0-dev,true,host,host.domain,keyword,extended,,CONTOSO,Name of the directory the group is a member of.
9.2.0-dev,true,host,host.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,host,host.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,host,host.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,host,host.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,host,host.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,host,host.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,host,host.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,host,host.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,host,host.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,host,host.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,host,host.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,host,host.hostname,keyword,core,,,Hostname of the host.
9.2.0-dev,true,host,host.id,keyword,core,,,Unique host id.
9.2.0-dev,true,host,host.ip,ip,core,array,,Host ip addresses.
9.2.0-dev,true,host,host.mac,keyword,core,array,"[""00-00-5E-00-53-23"", ""00-00-5E-00-53-24""]",Host MAC addresses.
9.2.0-dev,true,host,host.name,keyword,core,,,Name of the host.
9.2.0-dev,true,host,host.network.egress.bytes,long,extended,,,The number of bytes sent on all network interfaces.
9.2.0-dev,true,host,host.network.egress.packets,long,extended,,,The number of packets sent on all network interfaces.
9.2.0-dev,true,host,host.network.ingress.bytes,long,extended,,,The number of bytes received on all network interfaces.
9.2.0-dev,true,host,host.network.ingress.packets,long,extended,,,The number of packets received on all network interfaces.
9.2.0-dev,true,host,host.os.family,keyword,extended,,debian,"OS family (such as redhat, debian, freebsd, windows)."
9.2.0-dev,true,host,host.os.full,keyword,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,host,host.os.full.text,match_only_text,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,host,host.os.kernel,keyword,extended,,4.4.0-112-generic,Operating system kernel version as a raw string.
9.2.0-dev,true,host,host.os.name,keyword,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,host,host.os.name.text,match_only_text,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,host,host.os.platform,keyword,extended,,darwin,"Operating system platform (such centos, ubuntu, windows)."
9.2.0-dev,true,host,host.os.type,keyword,extended,,macos,"Which commercial OS family (one of: linux, macos, unix, windows, ios or android)."
9.2.0-dev,true,host,host.os.version,keyword,extended,,10.14.1,Operating system version as a raw string.
9.2.0-dev,true,host,host.pid_ns_ino,keyword,extended,,256383,Pid namespace inode
9.2.0-dev,true,host,host.risk.calculated_level,keyword,extended,,High,A risk classification level calculated by an internal system as part of entity analytics and entity risk scoring.
9.2.0-dev,true,host,host.risk.calculated_score,float,extended,,880.73,A risk classification score calculated by an internal system as part of entity analytics and entity risk scoring.
9.2.0-dev,true,host,host.risk.calculated_score_norm,float,extended,,88.73,A normalized risk score calculated by an internal system.
9.2.0-dev,true,host,host.risk.static_level,keyword,extended,,High,"A risk classification level obtained from outside the system, such as from some external Threat Intelligence Platform."
9.2.0-dev,true,host,host.risk.static_score,float,extended,,830.0,"A risk classification score obtained from outside the system, such as from some external Threat Intelligence Platform."
9.2.0-dev,true,host,host.risk.static_score_norm,float,extended,,83.0,A normalized risk score calculated by an external system.
9.2.0-dev,true,host,host.type,keyword,core,,,Type of host.
9.2.0-dev,true,host,host.uptime,long,extended,,1325,Seconds the host has been up.
9.2.0-dev,true,http,http.request.body.bytes,long,extended,,887,Size in bytes of the request body.
9.2.0-dev,true,http,http.request.body.content,wildcard,extended,,Hello world,The full HTTP request body.
9.2.0-dev,true,http,http.request.body.content.text,match_only_text,extended,,Hello world,The full HTTP request body.
9.2.0-dev,true,http,http.request.bytes,long,extended,,1437,Total size in bytes of the request (body and headers).
9.2.0-dev,true,http,http.request.id,keyword,extended,,123e4567-e89b-12d3-a456-426614174000,HTTP request ID.
9.2.0-dev,true,http,http.request.method,keyword,extended,,POST,HTTP request method.
9.2.0-dev,true,http,http.request.mime_type,keyword,extended,,image/gif,Mime type of the body of the request.
9.2.0-dev,true,http,http.request.referrer,keyword,extended,,https://blog.example.com/,Referrer for this HTTP request.
9.2.0-dev,true,http,http.response.body.bytes,long,extended,,887,Size in bytes of the response body.
9.2.0-dev,true,http,http.response.body.content,wildcard,extended,,Hello world,The full HTTP response body.
9.2.0-dev,true,http,http.response.body.content.text,match_only_text,extended,,Hello world,The full HTTP response body.
9.2.0-dev,true,http,http.response.bytes,long,extended,,1437,Total size in bytes of the response (body and headers).
9.2.0-dev,true,http,http.response.mime_type,keyword,extended,,image/gif,Mime type of the body of the response.
9.2.0-dev,true,http,http.response.status_code,long,extended,,404,HTTP response status code.
9.2.0-dev,true,http,http.version,keyword,extended,,1.1,HTTP version.
9.2.0-dev,true,log,log.file.path,keyword,extended,,/var/log/fun-times.log,Full path to the log file this event came from.
9.2.0-dev,true,log,log.level,keyword,core,,error,Log level of the log event.
9.2.0-dev,true,log,log.logger,keyword,core,,org.elasticsearch.bootstrap.Bootstrap,Name of the logger.
9.2.0-dev,true,log,log.origin.file.line,long,extended,,42,The line number of the file which originated the log event.
9.2.0-dev,true,log,log.origin.file.name,keyword,extended,,Bootstrap.java,The code file which originated the log event.
9.2.0-dev,true,log,log.origin.function,keyword,extended,,init,The function which originated the log event.
9.2.0-dev,true,log,log.syslog,object,extended,,,Syslog metadata
9.2.0-dev,true,log,log.syslog.appname,keyword,extended,,sshd,The device or application that originated the Syslog message.
9.2.0-dev,true,log,log.syslog.facility.code,long,extended,,23,Syslog numeric facility of the event.
9.2.0-dev,true,log,log.syslog.facility.name,keyword,extended,,local7,Syslog text-based facility of the event.
9.2.0-dev,true,log,log.syslog.hostname,keyword,extended,,example-host,The host that originated the Syslog message.
9.2.0-dev,true,log,log.syslog.msgid,keyword,extended,,ID47,An identifier for the type of Syslog message.
9.2.0-dev,true,log,log.syslog.priority,long,extended,,135,Syslog priority of the event.
9.2.0-dev,true,log,log.syslog.procid,keyword,extended,,12345,The process name or ID that originated the Syslog message.
9.2.0-dev,true,log,log.syslog.severity.code,long,extended,,3,Syslog numeric severity of the event.
9.2.0-dev,true,log,log.syslog.severity.name,keyword,extended,,Error,Syslog text-based severity of the event.
9.2.0-dev,true,log,log.syslog.structured_data,flattened,extended,,,Structured data expressed in RFC 5424 messages.
9.2.0-dev,true,log,log.syslog.version,keyword,extended,,1,Syslog protocol version.
9.2.0-dev,true,network,network.application,keyword,extended,,aim,Application level protocol name.
9.2.0-dev,true,network,network.bytes,long,core,,368,Total bytes transferred in both directions.
9.2.0-dev,true,network,network.community_id,keyword,extended,,1:hO+sN4H+MG5MY/8hIrXPqc4ZQz0=,A hash of source and destination IPs and ports.
9.2.0-dev,true,network,network.direction,keyword,core,,inbound,Direction of the network traffic.
9.2.0-dev,true,network,network.forwarded_ip,ip,core,,192.1.1.2,Host IP address when the source IP address is the proxy.
9.2.0-dev,true,network,network.iana_number,keyword,extended,,6,IANA Protocol Number.
9.2.0-dev,true,network,network.inner,object,extended,,,Inner VLAN tag information
9.2.0-dev,true,network,network.inner.vlan.id,keyword,extended,,10,VLAN ID as reported by the observer.
9.2.0-dev,true,network,network.inner.vlan.name,keyword,extended,,outside,Optional VLAN name as reported by the observer.
9.2.0-dev,true,network,network.name,keyword,extended,,Guest Wifi,Name given by operators to sections of their network.
9.2.0-dev,true,network,network.packets,long,core,,24,Total packets transferred in both directions.
9.2.0-dev,true,network,network.protocol,keyword,core,,http,Application protocol name.
9.2.0-dev,true,network,network.transport,keyword,core,,tcp,Protocol Name corresponding to the field `iana_number`.
9.2.0-dev,true,network,network.type,keyword,core,,ipv4,"In the OSI Model this would be the Network Layer. ipv4, ipv6, ipsec, pim, etc"
9.2.0-dev,true,network,network.vlan.id,keyword,extended,,10,VLAN ID as reported by the observer.
9.2.0-dev,true,network,network.vlan.name,keyword,extended,,outside,Optional VLAN name as reported by the observer.
9.2.0-dev,true,observer,observer.egress,object,extended,,,Object field for egress information
9.2.0-dev,true,observer,observer.egress.interface.alias,keyword,extended,,outside,Interface alias
9.2.0-dev,true,observer,observer.egress.interface.id,keyword,extended,,10,Interface ID
9.2.0-dev,true,observer,observer.egress.interface.name,keyword,extended,,eth0,Interface name
9.2.0-dev,true,observer,observer.egress.vlan.id,keyword,extended,,10,VLAN ID as reported by the observer.
9.2.0-dev,true,observer,observer.egress.vlan.name,keyword,extended,,outside,Optional VLAN name as reported by the observer.
9.2.0-dev,true,observer,observer.egress.zone,keyword,extended,,Public_Internet,Observer Egress zone
9.2.0-dev,true,observer,observer.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,observer,observer.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,observer,observer.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,observer,observer.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,observer,observer.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,observer,observer.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,observer,observer.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,observer,observer.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,observer,observer.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,observer,observer.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,observer,observer.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,observer,observer.hostname,keyword,core,,,Hostname of the observer.
9.2.0-dev,true,observer,observer.ingress,object,extended,,,Object field for ingress information
9.2.0-dev,true,observer,observer.ingress.interface.alias,keyword,extended,,outside,Interface alias
9.2.0-dev,true,observer,observer.ingress.interface.id,keyword,extended,,10,Interface ID
9.2.0-dev,true,observer,observer.ingress.interface.name,keyword,extended,,eth0,Interface name
9.2.0-dev,true,observer,observer.ingress.vlan.id,keyword,extended,,10,VLAN ID as reported by the observer.
9.2.0-dev,true,observer,observer.ingress.vlan.name,keyword,extended,,outside,Optional VLAN name as reported by the observer.
9.2.0-dev,true,observer,observer.ingress.zone,keyword,extended,,DMZ,Observer ingress zone
9.2.0-dev,true,observer,observer.ip,ip,core,array,,IP addresses of the observer.
9.2.0-dev,true,observer,observer.mac,keyword,core,array,"[""00-00-5E-00-53-23"", ""00-00-5E-00-53-24""]",MAC addresses of the observer.
9.2.0-dev,true,observer,observer.name,keyword,extended,,1_proxySG,Custom name of the observer.
9.2.0-dev,true,observer,observer.os.family,keyword,extended,,debian,"OS family (such as redhat, debian, freebsd, windows)."
9.2.0-dev,true,observer,observer.os.full,keyword,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,observer,observer.os.full.text,match_only_text,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,observer,observer.os.kernel,keyword,extended,,4.4.0-112-generic,Operating system kernel version as a raw string.
9.2.0-dev,true,observer,observer.os.name,keyword,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,observer,observer.os.name.text,match_only_text,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,observer,observer.os.platform,keyword,extended,,darwin,"Operating system platform (such centos, ubuntu, windows)."
9.2.0-dev,true,observer,observer.os.type,keyword,extended,,macos,"Which commercial OS family (one of: linux, macos, unix, windows, ios or android)."
9.2.0-dev,true,observer,observer.os.version,keyword,extended,,10.14.1,Operating system version as a raw string.
9.2.0-dev,true,observer,observer.product,keyword,extended,,s200,The product name of the observer.
9.2.0-dev,true,observer,observer.serial_number,keyword,extended,,,Observer serial number.
9.2.0-dev,true,observer,observer.type,keyword,core,,firewall,The type of the observer the data is coming from.
9.2.0-dev,true,observer,observer.vendor,keyword,core,,Symantec,Vendor name of the observer.
9.2.0-dev,true,observer,observer.version,keyword,core,,,Observer version.
9.2.0-dev,true,orchestrator,orchestrator.api_version,keyword,extended,,v1beta1,API version being used to carry out the action
9.2.0-dev,true,orchestrator,orchestrator.cluster.id,keyword,extended,,,Unique ID of the cluster.
9.2.0-dev,true,orchestrator,orchestrator.cluster.name,keyword,extended,,,Name of the cluster.
9.2.0-dev,true,orchestrator,orchestrator.cluster.url,keyword,extended,,,URL of the API used to manage the cluster.
9.2.0-dev,true,orchestrator,orchestrator.cluster.version,keyword,extended,,,The version of the cluster.
9.2.0-dev,true,orchestrator,orchestrator.namespace,keyword,extended,,kube-system,Namespace in which the action is taking place.
9.2.0-dev,true,orchestrator,orchestrator.organization,keyword,extended,,elastic,Organization affected by the event (for multi-tenant orchestrator setups).
9.2.0-dev,true,orchestrator,orchestrator.resource.annotation,keyword,extended,array,"['key1:value1', 'key2:value2', 'key3:value3']",The list of annotations added to the resource.
9.2.0-dev,true,orchestrator,orchestrator.resource.id,keyword,extended,,,Unique ID of the resource being acted upon.
9.2.0-dev,true,orchestrator,orchestrator.resource.ip,ip,extended,array,,IP address assigned to the resource associated with the event being observed.
9.2.0-dev,true,orchestrator,orchestrator.resource.label,keyword,extended,array,"['key1:value1', 'key2:value2', 'key3:value3']",The list of labels added to the resource.
9.2.0-dev,true,orchestrator,orchestrator.resource.name,keyword,extended,,test-pod-cdcws,Name of the resource being acted upon.
9.2.0-dev,true,orchestrator,orchestrator.resource.parent.type,keyword,extended,,DaemonSet,Type or kind of the parent resource associated with the event being observed.
9.2.0-dev,true,orchestrator,orchestrator.resource.type,keyword,extended,,service,Type of resource being acted upon.
9.2.0-dev,true,orchestrator,orchestrator.type,keyword,extended,,kubernetes,"Orchestrator cluster type (e.g. kubernetes, nomad or cloudfoundry)."
9.2.0-dev,true,organization,organization.id,keyword,extended,,,Unique identifier for the organization.
9.2.0-dev,true,organization,organization.name,keyword,extended,,,Organization name.
9.2.0-dev,true,organization,organization.name.text,match_only_text,extended,,,Organization name.
9.2.0-dev,true,package,package.architecture,keyword,extended,,x86_64,Package architecture.
9.2.0-dev,true,package,package.build_version,keyword,extended,,36f4f7e89dd61b0988b12ee000b98966867710cd,Build version information
9.2.0-dev,true,package,package.checksum,keyword,extended,,68b329da9893e34099c7d8ad5cb9c940,Checksum of the installed package for verification.
9.2.0-dev,true,package,package.description,keyword,extended,,Open source programming language to build simple/reliable/efficient software.,Description of the package.
9.2.0-dev,true,package,package.install_scope,keyword,extended,,global,"Indicating how the package was installed, e.g. user-local, global."
9.2.0-dev,true,package,package.installed,date,extended,,,Time when package was installed.
9.2.0-dev,true,package,package.license,keyword,extended,,Apache License 2.0,Package license
9.2.0-dev,true,package,package.name,keyword,extended,,go,Package name
9.2.0-dev,true,package,package.path,keyword,extended,,/usr/local/Cellar/go/1.12.9/,Path where the package is installed.
9.2.0-dev,true,package,package.reference,keyword,extended,,https://golang.org,Package home page or reference URL
9.2.0-dev,true,package,package.size,long,extended,,62231,Package size in bytes.
9.2.0-dev,true,package,package.type,keyword,extended,,rpm,Package type
9.2.0-dev,true,package,package.version,keyword,extended,,1.12.9,Package version
9.2.0-dev,true,process,process.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,process,process.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,process,process.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,process,process.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,process,process.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,process,process.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,process,process.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,process,process.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,process,process.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,process,process.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,process,process.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,process,process.command_line,wildcard,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.command_line.text,match_only_text,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.elf.architecture,keyword,extended,,x86-64,Machine architecture of the ELF file.
9.2.0-dev,true,process,process.elf.byte_order,keyword,extended,,Little Endian,Byte sequence of ELF file.
9.2.0-dev,true,process,process.elf.cpu_type,keyword,extended,,Intel,CPU type of the ELF file.
9.2.0-dev,true,process,process.elf.creation_date,date,extended,,,Build or compile date.
9.2.0-dev,true,process,process.elf.exports,flattened,extended,array,,List of exported element names and types.
9.2.0-dev,true,process,process.elf.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in an ELF file.
9.2.0-dev,true,process,process.elf.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.elf.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.elf.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.elf.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.elf.header.abi_version,keyword,extended,,,Version of the ELF Application Binary Interface (ABI).
9.2.0-dev,true,process,process.elf.header.class,keyword,extended,,,Header class of the ELF file.
9.2.0-dev,true,process,process.elf.header.data,keyword,extended,,,Data table of the ELF header.
9.2.0-dev,true,process,process.elf.header.entrypoint,long,extended,,,Header entrypoint of the ELF file.
9.2.0-dev,true,process,process.elf.header.object_version,keyword,extended,,,"""0x1"" for original ELF files."
9.2.0-dev,true,process,process.elf.header.os_abi,keyword,extended,,,Application Binary Interface (ABI) of the Linux OS.
9.2.0-dev,true,process,process.elf.header.type,keyword,extended,,,Header type of the ELF file.
9.2.0-dev,true,process,process.elf.header.version,keyword,extended,,,Version of the ELF header.
9.2.0-dev,true,process,process.elf.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in an ELF file.
9.2.0-dev,true,process,process.elf.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.elf.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.elf.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.elf.sections,nested,extended,array,,Section information of the ELF file.
9.2.0-dev,true,process,process.elf.sections.chi2,long,extended,,,Chi-square probability distribution of the section.
9.2.0-dev,true,process,process.elf.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.elf.sections.flags,keyword,extended,,,ELF Section List flags.
9.2.0-dev,true,process,process.elf.sections.name,keyword,extended,,,ELF Section List name.
9.2.0-dev,true,process,process.elf.sections.physical_offset,keyword,extended,,,ELF Section List offset.
9.2.0-dev,true,process,process.elf.sections.physical_size,long,extended,,,ELF Section List physical size.
9.2.0-dev,true,process,process.elf.sections.type,keyword,extended,,,ELF Section List type.
9.2.0-dev,true,process,process.elf.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.elf.sections.virtual_address,long,extended,,,ELF Section List virtual address.
9.2.0-dev,true,process,process.elf.sections.virtual_size,long,extended,,,ELF Section List virtual size.
9.2.0-dev,true,process,process.elf.segments,nested,extended,array,,ELF object segment list.
9.2.0-dev,true,process,process.elf.segments.sections,keyword,extended,,,ELF object segment sections.
9.2.0-dev,true,process,process.elf.segments.type,keyword,extended,,,ELF object segment type.
9.2.0-dev,true,process,process.elf.shared_libraries,keyword,extended,array,,List of shared libraries used by this ELF object.
9.2.0-dev,true,process,process.elf.telfhash,keyword,extended,,,telfhash hash for ELF file.
9.2.0-dev,true,process,process.end,date,extended,,2016-05-23T08:05:34.853Z,The time the process ended.
9.2.0-dev,true,process,process.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.entry_leader.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.entry_leader.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.entry_leader.attested_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.entry_leader.attested_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.entry_leader.attested_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.attested_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.command_line,wildcard,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.entry_leader.command_line.text,match_only_text,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.entry_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.entry_leader.entry_meta.source.ip,ip,core,,,IP address of the source.
9.2.0-dev,true,process,process.entry_leader.entry_meta.type,keyword,extended,,,The entry type for the entry session leader.
9.2.0-dev,true,process,process.entry_leader.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.entry_leader.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.entry_leader.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.entry_leader.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.entry_leader.interactive,boolean,extended,,True,Whether the process is connected to an interactive shell.
9.2.0-dev,true,process,process.entry_leader.name,keyword,extended,,ssh,Process name.
9.2.0-dev,true,process,process.entry_leader.name.text,match_only_text,extended,,ssh,Process name.
9.2.0-dev,true,process,process.entry_leader.parent.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.entry_leader.parent.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.entry_leader.parent.session_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.entry_leader.parent.session_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.entry_leader.parent.session_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.entry_leader.parent.session_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.entry_leader.parent.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.entry_leader.parent.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.entry_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.entry_leader.real_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.entry_leader.real_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.entry_leader.real_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.entry_leader.real_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.real_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.same_as_process,boolean,extended,,True,This boolean is used to identify if a leader process is the same as the top level process.
9.2.0-dev,true,process,process.entry_leader.saved_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.entry_leader.saved_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.entry_leader.saved_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.entry_leader.saved_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.saved_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.entry_leader.supplemental_groups.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.entry_leader.supplemental_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.entry_leader.tty,object,extended,,,Information about the controlling TTY device.
9.2.0-dev,true,process,process.entry_leader.tty.char_device.major,long,extended,,4,The TTY character device's major number.
9.2.0-dev,true,process,process.entry_leader.tty.char_device.minor,long,extended,,1,The TTY character device's minor number.
9.2.0-dev,true,process,process.entry_leader.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.entry_leader.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.entry_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.entry_leader.working_directory,keyword,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.entry_leader.working_directory.text,match_only_text,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.env_vars,keyword,extended,array,"[""PATH=/usr/local/bin:/usr/bin"", ""USER=ubuntu""]",Array of environment variable bindings.
9.2.0-dev,true,process,process.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.exit_code,long,extended,,137,The exit code of the process.
9.2.0-dev,true,process,process.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.group_leader.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.group_leader.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.group_leader.command_line,wildcard,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.group_leader.command_line.text,match_only_text,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.group_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.group_leader.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.group_leader.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.group_leader.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.group_leader.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.group_leader.interactive,boolean,extended,,True,Whether the process is connected to an interactive shell.
9.2.0-dev,true,process,process.group_leader.name,keyword,extended,,ssh,Process name.
9.2.0-dev,true,process,process.group_leader.name.text,match_only_text,extended,,ssh,Process name.
9.2.0-dev,true,process,process.group_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.group_leader.real_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.group_leader.real_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.group_leader.real_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.group_leader.real_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.real_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.same_as_process,boolean,extended,,True,This boolean is used to identify if a leader process is the same as the top level process.
9.2.0-dev,true,process,process.group_leader.saved_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.group_leader.saved_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.group_leader.saved_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.group_leader.saved_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.saved_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.group_leader.supplemental_groups.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.group_leader.supplemental_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.group_leader.tty,object,extended,,,Information about the controlling TTY device.
9.2.0-dev,true,process,process.group_leader.tty.char_device.major,long,extended,,4,The TTY character device's major number.
9.2.0-dev,true,process,process.group_leader.tty.char_device.minor,long,extended,,1,The TTY character device's minor number.
9.2.0-dev,true,process,process.group_leader.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.group_leader.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.group_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.group_leader.working_directory,keyword,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.group_leader.working_directory.text,match_only_text,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,process,process.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,process,process.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,process,process.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,process,process.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,process,process.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,process,process.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,process,process.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,process,process.interactive,boolean,extended,,True,Whether the process is connected to an interactive shell.
9.2.0-dev,true,process,process.io,object,extended,,,A chunk of input or output (IO) from a single process.
9.2.0-dev,true,process,process.io.bytes_skipped,object,extended,array,,An array of byte offsets and lengths denoting where IO data has been skipped.
9.2.0-dev,true,process,process.io.bytes_skipped.length,long,extended,,,The length of bytes skipped.
9.2.0-dev,true,process,process.io.bytes_skipped.offset,long,extended,,,The byte offset into this event's io.text (or io.bytes in the future) where length bytes were skipped.
9.2.0-dev,true,process,process.io.max_bytes_per_process_exceeded,boolean,extended,,,"If true, the process producing the output has exceeded the max_kilobytes_per_process configuration setting."
9.2.0-dev,true,process,process.io.text,wildcard,extended,,,A chunk of output or input sanitized to UTF-8.
9.2.0-dev,true,process,process.io.total_bytes_captured,long,extended,,,The total number of bytes captured in this event.
9.2.0-dev,true,process,process.io.total_bytes_skipped,long,extended,,,The total number of bytes that were not captured due to implementation restrictions such as buffer size limits.
9.2.0-dev,true,process,process.io.type,keyword,extended,,,The type of object on which the IO action (read or write) was taken.
9.2.0-dev,true,process,process.macho.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a Mach-O file.
9.2.0-dev,true,process,process.macho.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.macho.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.macho.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.macho.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.macho.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a Mach-O file.
9.2.0-dev,true,process,process.macho.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.macho.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.macho.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.macho.sections,nested,extended,array,,Section information of the Mach-O file.
9.2.0-dev,true,process,process.macho.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.macho.sections.name,keyword,extended,,,Mach-O Section List name.
9.2.0-dev,true,process,process.macho.sections.physical_size,long,extended,,,Mach-O Section List physical size.
9.2.0-dev,true,process,process.macho.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.macho.sections.virtual_size,long,extended,,,Mach-O Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,process,process.macho.symhash,keyword,extended,,d3ccf195b62a9279c3c19af1080497ec,A hash of the imports in a Mach-O file.
9.2.0-dev,true,process,process.name,keyword,extended,,ssh,Process name.
9.2.0-dev,true,process,process.name.text,match_only_text,extended,,ssh,Process name.
9.2.0-dev,true,process,process.parent.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.parent.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.parent.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,process,process.parent.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,process,process.parent.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,process,process.parent.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,process,process.parent.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,process,process.parent.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,process,process.parent.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,process,process.parent.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,process,process.parent.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,process,process.parent.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,process,process.parent.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,process,process.parent.command_line,wildcard,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.parent.command_line.text,match_only_text,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.parent.elf.architecture,keyword,extended,,x86-64,Machine architecture of the ELF file.
9.2.0-dev,true,process,process.parent.elf.byte_order,keyword,extended,,Little Endian,Byte sequence of ELF file.
9.2.0-dev,true,process,process.parent.elf.cpu_type,keyword,extended,,Intel,CPU type of the ELF file.
9.2.0-dev,true,process,process.parent.elf.creation_date,date,extended,,,Build or compile date.
9.2.0-dev,true,process,process.parent.elf.exports,flattened,extended,array,,List of exported element names and types.
9.2.0-dev,true,process,process.parent.elf.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in an ELF file.
9.2.0-dev,true,process,process.parent.elf.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.parent.elf.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.elf.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.elf.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.parent.elf.header.abi_version,keyword,extended,,,Version of the ELF Application Binary Interface (ABI).
9.2.0-dev,true,process,process.parent.elf.header.class,keyword,extended,,,Header class of the ELF file.
9.2.0-dev,true,process,process.parent.elf.header.data,keyword,extended,,,Data table of the ELF header.
9.2.0-dev,true,process,process.parent.elf.header.entrypoint,long,extended,,,Header entrypoint of the ELF file.
9.2.0-dev,true,process,process.parent.elf.header.object_version,keyword,extended,,,"""0x1"" for original ELF files."
9.2.0-dev,true,process,process.parent.elf.header.os_abi,keyword,extended,,,Application Binary Interface (ABI) of the Linux OS.
9.2.0-dev,true,process,process.parent.elf.header.type,keyword,extended,,,Header type of the ELF file.
9.2.0-dev,true,process,process.parent.elf.header.version,keyword,extended,,,Version of the ELF header.
9.2.0-dev,true,process,process.parent.elf.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in an ELF file.
9.2.0-dev,true,process,process.parent.elf.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.parent.elf.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.elf.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.elf.sections,nested,extended,array,,Section information of the ELF file.
9.2.0-dev,true,process,process.parent.elf.sections.chi2,long,extended,,,Chi-square probability distribution of the section.
9.2.0-dev,true,process,process.parent.elf.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.elf.sections.flags,keyword,extended,,,ELF Section List flags.
9.2.0-dev,true,process,process.parent.elf.sections.name,keyword,extended,,,ELF Section List name.
9.2.0-dev,true,process,process.parent.elf.sections.physical_offset,keyword,extended,,,ELF Section List offset.
9.2.0-dev,true,process,process.parent.elf.sections.physical_size,long,extended,,,ELF Section List physical size.
9.2.0-dev,true,process,process.parent.elf.sections.type,keyword,extended,,,ELF Section List type.
9.2.0-dev,true,process,process.parent.elf.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.elf.sections.virtual_address,long,extended,,,ELF Section List virtual address.
9.2.0-dev,true,process,process.parent.elf.sections.virtual_size,long,extended,,,ELF Section List virtual size.
9.2.0-dev,true,process,process.parent.elf.segments,nested,extended,array,,ELF object segment list.
9.2.0-dev,true,process,process.parent.elf.segments.sections,keyword,extended,,,ELF object segment sections.
9.2.0-dev,true,process,process.parent.elf.segments.type,keyword,extended,,,ELF object segment type.
9.2.0-dev,true,process,process.parent.elf.shared_libraries,keyword,extended,array,,List of shared libraries used by this ELF object.
9.2.0-dev,true,process,process.parent.elf.telfhash,keyword,extended,,,telfhash hash for ELF file.
9.2.0-dev,true,process,process.parent.end,date,extended,,2016-05-23T08:05:34.853Z,The time the process ended.
9.2.0-dev,true,process,process.parent.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.parent.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.parent.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.parent.exit_code,long,extended,,137,The exit code of the process.
9.2.0-dev,true,process,process.parent.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.parent.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.parent.group_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.parent.group_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.parent.group_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.parent.group_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.parent.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,process,process.parent.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,process,process.parent.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,process,process.parent.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,process,process.parent.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,process,process.parent.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,process,process.parent.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,process,process.parent.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,process,process.parent.interactive,boolean,extended,,True,Whether the process is connected to an interactive shell.
9.2.0-dev,true,process,process.parent.macho.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a Mach-O file.
9.2.0-dev,true,process,process.parent.macho.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.parent.macho.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.macho.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.macho.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.parent.macho.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a Mach-O file.
9.2.0-dev,true,process,process.parent.macho.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.parent.macho.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.macho.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.macho.sections,nested,extended,array,,Section information of the Mach-O file.
9.2.0-dev,true,process,process.parent.macho.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.macho.sections.name,keyword,extended,,,Mach-O Section List name.
9.2.0-dev,true,process,process.parent.macho.sections.physical_size,long,extended,,,Mach-O Section List physical size.
9.2.0-dev,true,process,process.parent.macho.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.macho.sections.virtual_size,long,extended,,,Mach-O Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,process,process.parent.macho.symhash,keyword,extended,,d3ccf195b62a9279c3c19af1080497ec,A hash of the imports in a Mach-O file.
9.2.0-dev,true,process,process.parent.name,keyword,extended,,ssh,Process name.
9.2.0-dev,true,process,process.parent.name.text,match_only_text,extended,,ssh,Process name.
9.2.0-dev,true,process,process.parent.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,process,process.parent.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,process,process.parent.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,process,process.parent.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,process,process.parent.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,process,process.parent.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.parent.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.parent.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.parent.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,process,process.parent.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,process,process.parent.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.parent.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.parent.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,process,process.parent.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,process,process.parent.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,process,process.parent.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,process,process.parent.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,process,process.parent.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,process,process.parent.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.parent.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,process,process.parent.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.parent.real_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.parent.real_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.parent.real_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.parent.real_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.real_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.saved_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.parent.saved_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.parent.saved_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.parent.saved_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.saved_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.parent.supplemental_groups.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.parent.supplemental_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.parent.thread.capabilities.effective,keyword,extended,array,"[""CAP_BPF"", ""CAP_SYS_ADMIN""]",Array of capabilities used for permission checks.
9.2.0-dev,true,process,process.parent.thread.capabilities.permitted,keyword,extended,array,"[""CAP_BPF"", ""CAP_SYS_ADMIN""]",Array of capabilities a thread could assume.
9.2.0-dev,true,process,process.parent.thread.id,long,extended,,4242,Thread ID.
9.2.0-dev,true,process,process.parent.thread.name,keyword,extended,,thread-0,Thread name.
9.2.0-dev,true,process,process.parent.title,keyword,extended,,,Process title.
9.2.0-dev,true,process,process.parent.title.text,match_only_text,extended,,,Process title.
9.2.0-dev,true,process,process.parent.tty,object,extended,,,Information about the controlling TTY device.
9.2.0-dev,true,process,process.parent.tty.char_device.major,long,extended,,4,The TTY character device's major number.
9.2.0-dev,true,process,process.parent.tty.char_device.minor,long,extended,,1,The TTY character device's minor number.
9.2.0-dev,true,process,process.parent.uptime,long,extended,,1325,Seconds the process has been up.
9.2.0-dev,true,process,process.parent.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.parent.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.parent.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.parent.working_directory,keyword,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.parent.working_directory.text,match_only_text,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,process,process.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,process,process.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,process,process.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,process,process.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,process,process.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,process,process.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,process,process.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,process,process.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,process,process.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,process,process.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,process,process.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,process,process.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,process,process.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,process,process.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,process,process.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,process,process.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,process,process.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,process,process.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,process,process.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,process,process.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.previous.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.previous.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.previous.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.previous.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.real_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.real_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.real_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.real_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.real_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.saved_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.saved_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.saved_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.saved_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.saved_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.args,keyword,extended,array,"[""/usr/bin/ssh"", ""-l"", ""user"", ""10.0.0.16""]",Array of process arguments.
9.2.0-dev,true,process,process.session_leader.args_count,long,extended,,4,Length of the process.args array.
9.2.0-dev,true,process,process.session_leader.command_line,wildcard,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.session_leader.command_line.text,match_only_text,extended,,/usr/bin/ssh -l user 10.0.0.16,Full command line that started the process.
9.2.0-dev,true,process,process.session_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.session_leader.executable,keyword,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.session_leader.executable.text,match_only_text,extended,,/usr/bin/ssh,Absolute path to the process executable.
9.2.0-dev,true,process,process.session_leader.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.session_leader.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.session_leader.interactive,boolean,extended,,True,Whether the process is connected to an interactive shell.
9.2.0-dev,true,process,process.session_leader.name,keyword,extended,,ssh,Process name.
9.2.0-dev,true,process,process.session_leader.name.text,match_only_text,extended,,ssh,Process name.
9.2.0-dev,true,process,process.session_leader.parent.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.session_leader.parent.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.session_leader.parent.session_leader.entity_id,keyword,extended,,c2c455d9f99375d,Unique identifier for the process.
9.2.0-dev,true,process,process.session_leader.parent.session_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.session_leader.parent.session_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.session_leader.parent.session_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.session_leader.parent.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.session_leader.parent.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.session_leader.pid,long,core,,4242,Process id.
9.2.0-dev,true,process,process.session_leader.real_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.session_leader.real_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.session_leader.real_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.session_leader.real_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.real_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.same_as_process,boolean,extended,,True,This boolean is used to identify if a leader process is the same as the top level process.
9.2.0-dev,true,process,process.session_leader.saved_group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.session_leader.saved_group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.session_leader.saved_user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.session_leader.saved_user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.saved_user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.session_leader.supplemental_groups.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.session_leader.supplemental_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.session_leader.tty,object,extended,,,Information about the controlling TTY device.
9.2.0-dev,true,process,process.session_leader.tty.char_device.major,long,extended,,4,The TTY character device's major number.
9.2.0-dev,true,process,process.session_leader.tty.char_device.minor,long,extended,,1,The TTY character device's minor number.
9.2.0-dev,true,process,process.session_leader.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.session_leader.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.session_leader.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.session_leader.working_directory,keyword,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.session_leader.working_directory.text,match_only_text,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.start,date,extended,,2016-05-23T08:05:34.853Z,The time the process started.
9.2.0-dev,true,process,process.supplemental_groups.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,process,process.supplemental_groups.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,process,process.thread.capabilities.effective,keyword,extended,array,"[""CAP_BPF"", ""CAP_SYS_ADMIN""]",Array of capabilities used for permission checks.
9.2.0-dev,true,process,process.thread.capabilities.permitted,keyword,extended,array,"[""CAP_BPF"", ""CAP_SYS_ADMIN""]",Array of capabilities a thread could assume.
9.2.0-dev,true,process,process.thread.id,long,extended,,4242,Thread ID.
9.2.0-dev,true,process,process.thread.name,keyword,extended,,thread-0,Thread name.
9.2.0-dev,true,process,process.title,keyword,extended,,,Process title.
9.2.0-dev,true,process,process.title.text,match_only_text,extended,,,Process title.
9.2.0-dev,true,process,process.tty,object,extended,,,Information about the controlling TTY device.
9.2.0-dev,true,process,process.tty.char_device.major,long,extended,,4,The TTY character device's major number.
9.2.0-dev,true,process,process.tty.char_device.minor,long,extended,,1,The TTY character device's minor number.
9.2.0-dev,true,process,process.tty.columns,long,extended,,80,The number of character columns per line. e.g terminal width
9.2.0-dev,true,process,process.tty.rows,long,extended,,24,The number of character rows in the terminal. e.g terminal height
9.2.0-dev,true,process,process.uptime,long,extended,,1325,Seconds the process has been up.
9.2.0-dev,true,process,process.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,process,process.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,process,process.vpid,long,core,,4242,Virtual process id.
9.2.0-dev,true,process,process.working_directory,keyword,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,process,process.working_directory.text,match_only_text,extended,,/home/alice,The working directory of the process.
9.2.0-dev,true,registry,registry.data.bytes,keyword,extended,,ZQBuAC0AVQBTAAAAZQBuAAAAAAA=,Original bytes written with base64 encoding.
9.2.0-dev,true,registry,registry.data.strings,wildcard,core,array,"[""C:\rta\red_ttp\bin\myapp.exe""]",List of strings representing what was written to the registry.
9.2.0-dev,true,registry,registry.data.type,keyword,core,,REG_SZ,Standard registry type for encoding contents
9.2.0-dev,true,registry,registry.hive,keyword,core,,HKLM,Abbreviated name for the hive.
9.2.0-dev,true,registry,registry.key,keyword,core,,SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe,Hive-relative path of keys.
9.2.0-dev,true,registry,registry.path,keyword,core,,HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe\Debugger,"Full path, including hive, key and value"
9.2.0-dev,true,registry,registry.value,keyword,core,,Debugger,Name of the value written.
9.2.0-dev,true,related,related.hash,keyword,extended,array,,All the hashes seen on your event.
9.2.0-dev,true,related,related.hosts,keyword,extended,array,,All the host identifiers seen on your event.
9.2.0-dev,true,related,related.ip,ip,extended,array,,All of the IPs seen on your event.
9.2.0-dev,true,related,related.user,keyword,extended,array,,All the user names or other user identifiers seen on the event.
9.2.0-dev,true,rule,rule.author,keyword,extended,array,"[""Star-Lord""]",Rule author
9.2.0-dev,true,rule,rule.category,keyword,extended,,Attempted Information Leak,Rule category
9.2.0-dev,true,rule,rule.description,keyword,extended,,Block requests to public DNS over HTTPS / TLS protocols,Rule description
9.2.0-dev,true,rule,rule.id,keyword,extended,,101,Rule ID
9.2.0-dev,true,rule,rule.license,keyword,extended,,Apache 2.0,Rule license
9.2.0-dev,true,rule,rule.name,keyword,extended,,BLOCK_DNS_over_TLS,Rule name
9.2.0-dev,true,rule,rule.reference,keyword,extended,,https://en.wikipedia.org/wiki/DNS_over_TLS,Rule reference URL
9.2.0-dev,true,rule,rule.ruleset,keyword,extended,,Standard_Protocol_Filters,Rule ruleset
9.2.0-dev,true,rule,rule.uuid,keyword,extended,,1100110011,Rule UUID
9.2.0-dev,true,rule,rule.version,keyword,extended,,1.1,Rule version
9.2.0-dev,true,server,server.address,keyword,extended,,,Server network address.
9.2.0-dev,true,server,server.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,server,server.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,server,server.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,server,server.bytes,long,core,,184,Bytes sent from the server to the client.
9.2.0-dev,true,server,server.domain,keyword,core,,foo.example.com,The domain name of the server.
9.2.0-dev,true,server,server.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,server,server.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,server,server.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,server,server.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,server,server.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,server,server.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,server,server.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,server,server.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,server,server.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,server,server.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,server,server.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,server,server.ip,ip,core,,,IP address of the server.
9.2.0-dev,true,server,server.mac,keyword,core,,00-00-5E-00-53-23,MAC address of the server.
9.2.0-dev,true,server,server.nat.ip,ip,extended,,,Server NAT ip
9.2.0-dev,true,server,server.nat.port,long,extended,,,Server NAT port
9.2.0-dev,true,server,server.packets,long,core,,12,Packets sent from the server to the client.
9.2.0-dev,true,server,server.port,long,core,,,Port of the server.
9.2.0-dev,true,server,server.registered_domain,keyword,extended,,example.com,"The highest registered server domain, stripped of the subdomain."
9.2.0-dev,true,server,server.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,server,server.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,server,server.user.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,server,server.user.email,keyword,extended,,,User email address.
9.2.0-dev,true,server,server.user.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,server,server.user.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,server,server.user.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,server,server.user.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,server,server.user.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,server,server.user.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,server,server.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,server,server.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,server,server.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,server,server.user.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,service,service.address,keyword,extended,,172.26.0.2:5432,Address of this service.
9.2.0-dev,true,service,service.environment,keyword,extended,,production,Environment of the service.
9.2.0-dev,true,service,service.ephemeral_id,keyword,extended,,8a4f500f,Ephemeral identifier of this service.
9.2.0-dev,true,service,service.id,keyword,core,,d37e5ebfe0ae6c4972dbe9f0174a1637bb8247f6,Unique identifier of the running service.
9.2.0-dev,true,service,service.name,keyword,core,,elasticsearch-metrics,Name of the service.
9.2.0-dev,true,service,service.node.name,keyword,extended,,instance-0000000016,Name of the service node.
9.2.0-dev,true,service,service.node.role,keyword,extended,,background_tasks,Deprecated role (singular) of the service node.
9.2.0-dev,true,service,service.node.roles,keyword,extended,array,"[""ui"", ""background_tasks""]",Roles of the service node.
9.2.0-dev,true,service,service.origin.address,keyword,extended,,172.26.0.2:5432,Address of this service.
9.2.0-dev,true,service,service.origin.environment,keyword,extended,,production,Environment of the service.
9.2.0-dev,true,service,service.origin.ephemeral_id,keyword,extended,,8a4f500f,Ephemeral identifier of this service.
9.2.0-dev,true,service,service.origin.id,keyword,core,,d37e5ebfe0ae6c4972dbe9f0174a1637bb8247f6,Unique identifier of the running service.
9.2.0-dev,true,service,service.origin.name,keyword,core,,elasticsearch-metrics,Name of the service.
9.2.0-dev,true,service,service.origin.node.name,keyword,extended,,instance-0000000016,Name of the service node.
9.2.0-dev,true,service,service.origin.node.role,keyword,extended,,background_tasks,Deprecated role (singular) of the service node.
9.2.0-dev,true,service,service.origin.node.roles,keyword,extended,array,"[""ui"", ""background_tasks""]",Roles of the service node.
9.2.0-dev,true,service,service.origin.state,keyword,core,,,Current state of the service.
9.2.0-dev,true,service,service.origin.type,keyword,core,,elasticsearch,The type of the service.
9.2.0-dev,true,service,service.origin.version,keyword,core,,3.2.4,Version of the service.
9.2.0-dev,true,service,service.state,keyword,core,,,Current state of the service.
9.2.0-dev,true,service,service.target.address,keyword,extended,,172.26.0.2:5432,Address of this service.
9.2.0-dev,true,service,service.target.environment,keyword,extended,,production,Environment of the service.
9.2.0-dev,true,service,service.target.ephemeral_id,keyword,extended,,8a4f500f,Ephemeral identifier of this service.
9.2.0-dev,true,service,service.target.id,keyword,core,,d37e5ebfe0ae6c4972dbe9f0174a1637bb8247f6,Unique identifier of the running service.
9.2.0-dev,true,service,service.target.name,keyword,core,,elasticsearch-metrics,Name of the service.
9.2.0-dev,true,service,service.target.node.name,keyword,extended,,instance-0000000016,Name of the service node.
9.2.0-dev,true,service,service.target.node.role,keyword,extended,,background_tasks,Deprecated role (singular) of the service node.
9.2.0-dev,true,service,service.target.node.roles,keyword,extended,array,"[""ui"", ""background_tasks""]",Roles of the service node.
9.2.0-dev,true,service,service.target.state,keyword,core,,,Current state of the service.
9.2.0-dev,true,service,service.target.type,keyword,core,,elasticsearch,The type of the service.
9.2.0-dev,true,service,service.target.version,keyword,core,,3.2.4,Version of the service.
9.2.0-dev,true,service,service.type,keyword,core,,elasticsearch,The type of the service.
9.2.0-dev,true,service,service.version,keyword,core,,3.2.4,Version of the service.
9.2.0-dev,true,source,source.address,keyword,extended,,,Source network address.
9.2.0-dev,true,source,source.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,source,source.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,source,source.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,source,source.bytes,long,core,,184,Bytes sent from the source to the destination.
9.2.0-dev,true,source,source.domain,keyword,core,,foo.example.com,The domain name of the source.
9.2.0-dev,true,source,source.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,source,source.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,source,source.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,source,source.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,source,source.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,source,source.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,source,source.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,source,source.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,source,source.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,source,source.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,source,source.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,source,source.ip,ip,core,,,IP address of the source.
9.2.0-dev,true,source,source.mac,keyword,core,,00-00-5E-00-53-23,MAC address of the source.
9.2.0-dev,true,source,source.nat.ip,ip,extended,,,Source NAT ip
9.2.0-dev,true,source,source.nat.port,long,extended,,,Source NAT port
9.2.0-dev,true,source,source.packets,long,core,,12,Packets sent from the source to the destination.
9.2.0-dev,true,source,source.port,long,core,,,Port of the source.
9.2.0-dev,true,source,source.registered_domain,keyword,extended,,example.com,"The highest registered source domain, stripped of the subdomain."
9.2.0-dev,true,source,source.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,source,source.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,source,source.user.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,source,source.user.email,keyword,extended,,,User email address.
9.2.0-dev,true,source,source.user.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,source,source.user.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,source,source.user.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,source,source.user.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,source,source.user.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,source,source.user.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,source,source.user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,source,source.user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,source,source.user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,source,source.user.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,span,span.id,keyword,extended,,3ff9a8981b7ccd5a,Unique identifier of the span within the scope of its trace.
9.2.0-dev,true,threat,threat.enrichments,nested,extended,array,,List of objects containing indicators enriching the event.
9.2.0-dev,true,threat,threat.enrichments.indicator,object,extended,,,Object containing indicators enriching the event.
9.2.0-dev,true,threat,threat.enrichments.indicator.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,threat,threat.enrichments.indicator.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,threat,threat.enrichments.indicator.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,threat,threat.enrichments.indicator.confidence,keyword,extended,,Medium,Indicator confidence rating
9.2.0-dev,true,threat,threat.enrichments.indicator.description,keyword,extended,,IP x.x.x.x was observed delivering the Angler EK.,Indicator description
9.2.0-dev,true,threat,threat.enrichments.indicator.email.address,keyword,extended,,phish@example.com,Indicator email address
9.2.0-dev,true,threat,threat.enrichments.indicator.file.accessed,date,extended,,,Last time the file was accessed.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.attributes,keyword,extended,array,"[""readonly"", ""system""]",Array of file attributes.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.created,date,extended,,,File creation time.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.ctime,date,extended,,,Last time the file attributes or metadata changed.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.device,keyword,extended,,sda,Device that is the source of the file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.directory,keyword,extended,,/home/alice,Directory where the file is located.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.drive_letter,keyword,extended,,C,Drive letter where the file is located.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.architecture,keyword,extended,,x86-64,Machine architecture of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.byte_order,keyword,extended,,Little Endian,Byte sequence of ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.cpu_type,keyword,extended,,Intel,CPU type of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.creation_date,date,extended,,,Build or compile date.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.exports,flattened,extended,array,,List of exported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in an ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.abi_version,keyword,extended,,,Version of the ELF Application Binary Interface (ABI).
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.class,keyword,extended,,,Header class of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.data,keyword,extended,,,Data table of the ELF header.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.entrypoint,long,extended,,,Header entrypoint of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.object_version,keyword,extended,,,"""0x1"" for original ELF files."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.os_abi,keyword,extended,,,Application Binary Interface (ABI) of the Linux OS.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.type,keyword,extended,,,Header type of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.header.version,keyword,extended,,,Version of the ELF header.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in an ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections,nested,extended,array,,Section information of the ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.chi2,long,extended,,,Chi-square probability distribution of the section.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.flags,keyword,extended,,,ELF Section List flags.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.name,keyword,extended,,,ELF Section List name.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.physical_offset,keyword,extended,,,ELF Section List offset.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.physical_size,long,extended,,,ELF Section List physical size.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.type,keyword,extended,,,ELF Section List type.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.virtual_address,long,extended,,,ELF Section List virtual address.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.sections.virtual_size,long,extended,,,ELF Section List virtual size.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.segments,nested,extended,array,,ELF object segment list.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.segments.sections,keyword,extended,,,ELF object segment sections.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.segments.type,keyword,extended,,,ELF object segment type.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.shared_libraries,keyword,extended,array,,List of shared libraries used by this ELF object.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.elf.telfhash,keyword,extended,,,telfhash hash for ELF file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.extension,keyword,extended,,png,"File extension, excluding the leading dot."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.fork_name,keyword,extended,,Zone.Identifer,A fork is additional data associated with a filesystem object.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.gid,keyword,extended,,1001,Primary group ID (GID) of the file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.group,keyword,extended,,alice,Primary group name of the file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.inode,keyword,extended,,256383,Inode representing the file in the filesystem.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.mime_type,keyword,extended,,,"Media type of file, document, or arrangement of bytes."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.mode,keyword,extended,,0640,Mode of the file in octal representation.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.mtime,date,extended,,,Last time the file content was modified.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.name,keyword,extended,,example.png,"Name of the file including the extension, without the directory."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.origin_referrer_url,keyword,extended,,http://example.com/article1.html,The URL of the webpage that linked to the file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.origin_url,keyword,extended,,http://example.com/imgs/article1_img1.jpg,The URL where the file is hosted.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.owner,keyword,extended,,alice,File owner's username.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.path,keyword,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.path.text,match_only_text,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.size,long,extended,,16384,File size in bytes.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.target_path,keyword,extended,,,Target path for symlinks.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.target_path.text,match_only_text,extended,,,Target path for symlinks.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.type,keyword,extended,,file,"File type (file, dir, or symlink)."
9.2.0-dev,true,threat,threat.enrichments.indicator.file.uid,keyword,extended,,1001,The user ID (UID) or security identifier (SID) of the file owner.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,threat,threat.enrichments.indicator.file.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.enrichments.indicator.file.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,threat,threat.enrichments.indicator.first_seen,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was first reported.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,threat,threat.enrichments.indicator.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,threat,threat.enrichments.indicator.ip,ip,extended,,1.2.3.4,Indicator IP address
9.2.0-dev,true,threat,threat.enrichments.indicator.last_seen,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was last reported.
9.2.0-dev,true,threat,threat.enrichments.indicator.marking.tlp,keyword,extended,,CLEAR,Indicator TLP marking
9.2.0-dev,true,threat,threat.enrichments.indicator.marking.tlp_version,keyword,extended,,2.0,Indicator TLP version
9.2.0-dev,true,threat,threat.enrichments.indicator.modified_at,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was last updated.
9.2.0-dev,true,threat,threat.enrichments.indicator.name,keyword,extended,,5.2.75.227,Indicator display name
9.2.0-dev,true,threat,threat.enrichments.indicator.port,long,extended,,443,Indicator port
9.2.0-dev,true,threat,threat.enrichments.indicator.provider,keyword,extended,,lrz_urlhaus,Indicator provider
9.2.0-dev,true,threat,threat.enrichments.indicator.reference,keyword,extended,,https://system.example.com/indicator/0001234,Indicator reference URL
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.data.bytes,keyword,extended,,ZQBuAC0AVQBTAAAAZQBuAAAAAAA=,Original bytes written with base64 encoding.
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.data.strings,wildcard,core,array,"[""C:\rta\red_ttp\bin\myapp.exe""]",List of strings representing what was written to the registry.
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.data.type,keyword,core,,REG_SZ,Standard registry type for encoding contents
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.hive,keyword,core,,HKLM,Abbreviated name for the hive.
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.key,keyword,core,,SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe,Hive-relative path of keys.
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.path,keyword,core,,HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe\Debugger,"Full path, including hive, key and value"
9.2.0-dev,true,threat,threat.enrichments.indicator.registry.value,keyword,core,,Debugger,Name of the value written.
9.2.0-dev,true,threat,threat.enrichments.indicator.scanner_stats,long,extended,,4,Scanner statistics
9.2.0-dev,true,threat,threat.enrichments.indicator.sightings,long,extended,,20,Number of times indicator observed
9.2.0-dev,true,threat,threat.enrichments.indicator.type,keyword,extended,,ipv4-addr,Type of indicator
9.2.0-dev,true,threat,threat.enrichments.indicator.url.domain,keyword,extended,,www.elastic.co,Domain of the url.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.extension,keyword,extended,,png,"File extension from the request url, excluding the leading dot."
9.2.0-dev,true,threat,threat.enrichments.indicator.url.fragment,keyword,extended,,,Portion of the url after the `#`.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.full,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.full.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.original,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.original.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.password,keyword,extended,,,Password of the request.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.path,wildcard,extended,,,"Path of the request, such as ""/search""."
9.2.0-dev,true,threat,threat.enrichments.indicator.url.port,long,extended,,443,"Port of the request, such as 443."
9.2.0-dev,true,threat,threat.enrichments.indicator.url.query,keyword,extended,,,Query string of the request.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.registered_domain,keyword,extended,,example.com,"The highest registered url domain, stripped of the subdomain."
9.2.0-dev,true,threat,threat.enrichments.indicator.url.scheme,keyword,extended,,https,Scheme of the url.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,threat,threat.enrichments.indicator.url.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,threat,threat.enrichments.indicator.url.username,keyword,extended,,,Username of the request.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,threat,threat.enrichments.indicator.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.enrichments.indicator.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,threat,threat.enrichments.matched.atomic,keyword,extended,,bad-domain.com,Matched indicator value
9.2.0-dev,true,threat,threat.enrichments.matched.field,keyword,extended,,file.hash.sha256,Matched indicator field
9.2.0-dev,true,threat,threat.enrichments.matched.id,keyword,extended,,ff93aee5-86a1-4a61-b0e6-0cdc313d01b5,Matched indicator identifier
9.2.0-dev,true,threat,threat.enrichments.matched.index,keyword,extended,,filebeat-8.0.0-2021.05.23-000011,Matched indicator index
9.2.0-dev,true,threat,threat.enrichments.matched.occurred,date,extended,,2021-10-05T17:00:58.326Z,Date of match
9.2.0-dev,true,threat,threat.enrichments.matched.type,keyword,extended,,indicator_match_rule,Type of indicator match
9.2.0-dev,true,threat,threat.feed.dashboard_id,keyword,extended,,5ba16340-72e6-11eb-a3e3-b3cc7c78a70f,Feed dashboard ID.
9.2.0-dev,true,threat,threat.feed.description,keyword,extended,,Threat feed from the AlienVault Open Threat eXchange network.,Description of the threat feed.
9.2.0-dev,true,threat,threat.feed.name,keyword,extended,,AlienVault OTX,Name of the threat feed.
9.2.0-dev,true,threat,threat.feed.reference,keyword,extended,,https://otx.alienvault.com,Reference for the threat feed.
9.2.0-dev,true,threat,threat.framework,keyword,extended,,MITRE ATT&CK,Threat classification framework.
9.2.0-dev,true,threat,threat.group.alias,keyword,extended,array,"[ ""Magecart Group 6"" ]",Alias of the group.
9.2.0-dev,true,threat,threat.group.id,keyword,extended,,G0037,ID of the group.
9.2.0-dev,true,threat,threat.group.name,keyword,extended,,FIN6,Name of the group.
9.2.0-dev,true,threat,threat.group.reference,keyword,extended,,https://attack.mitre.org/groups/G0037/,Reference URL of the group.
9.2.0-dev,true,threat,threat.indicator.as.number,long,extended,,15169,Unique number allocated to the autonomous system.
9.2.0-dev,true,threat,threat.indicator.as.organization.name,keyword,extended,,Google LLC,Organization name.
9.2.0-dev,true,threat,threat.indicator.as.organization.name.text,match_only_text,extended,,Google LLC,Organization name.
9.2.0-dev,true,threat,threat.indicator.confidence,keyword,extended,,Medium,Indicator confidence rating
9.2.0-dev,true,threat,threat.indicator.description,keyword,extended,,IP x.x.x.x was observed delivering the Angler EK.,Indicator description
9.2.0-dev,true,threat,threat.indicator.email.address,keyword,extended,,phish@example.com,Indicator email address
9.2.0-dev,true,threat,threat.indicator.file.accessed,date,extended,,,Last time the file was accessed.
9.2.0-dev,true,threat,threat.indicator.file.attributes,keyword,extended,array,"[""readonly"", ""system""]",Array of file attributes.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.digest_algorithm,keyword,extended,,sha256,Hashing algorithm used to sign the process.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.exists,boolean,core,,true,Boolean to capture if a signature is present.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.flags,keyword,extended,,570522385,Code signing flags of the process
9.2.0-dev,true,threat,threat.indicator.file.code_signature.signing_id,keyword,extended,,com.apple.xpc.proxy,The identifier used to sign the process.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.status,keyword,extended,,ERROR_UNTRUSTED_ROOT,Additional information about the certificate status.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.subject_name,keyword,core,,Microsoft Corporation,Subject name of the code signer
9.2.0-dev,true,threat,threat.indicator.file.code_signature.team_id,keyword,extended,,EQHXZ8M8AV,The team identifier used to sign the process.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.thumbprint_sha256,keyword,extended,,c0f23a8eb1cba0ccaa88483b5a234c96e4bdfec719bf458024e68c2a8183476b,SHA256 hash of the certificate.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.timestamp,date,extended,,2021-01-01T12:10:30Z,When the signature was generated and signed.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.trusted,boolean,extended,,true,Stores the trust status of the certificate chain.
9.2.0-dev,true,threat,threat.indicator.file.code_signature.valid,boolean,extended,,true,Boolean to capture if the digital signature is verified against the binary content.
9.2.0-dev,true,threat,threat.indicator.file.created,date,extended,,,File creation time.
9.2.0-dev,true,threat,threat.indicator.file.ctime,date,extended,,,Last time the file attributes or metadata changed.
9.2.0-dev,true,threat,threat.indicator.file.device,keyword,extended,,sda,Device that is the source of the file.
9.2.0-dev,true,threat,threat.indicator.file.directory,keyword,extended,,/home/alice,Directory where the file is located.
9.2.0-dev,true,threat,threat.indicator.file.drive_letter,keyword,extended,,C,Drive letter where the file is located.
9.2.0-dev,true,threat,threat.indicator.file.elf.architecture,keyword,extended,,x86-64,Machine architecture of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.byte_order,keyword,extended,,Little Endian,Byte sequence of ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.cpu_type,keyword,extended,,Intel,CPU type of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.creation_date,date,extended,,,Build or compile date.
9.2.0-dev,true,threat,threat.indicator.file.elf.exports,flattened,extended,array,,List of exported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.elf.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in an ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,threat,threat.indicator.file.elf.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.indicator.file.elf.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.indicator.file.elf.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.abi_version,keyword,extended,,,Version of the ELF Application Binary Interface (ABI).
9.2.0-dev,true,threat,threat.indicator.file.elf.header.class,keyword,extended,,,Header class of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.data,keyword,extended,,,Data table of the ELF header.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.entrypoint,long,extended,,,Header entrypoint of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.object_version,keyword,extended,,,"""0x1"" for original ELF files."
9.2.0-dev,true,threat,threat.indicator.file.elf.header.os_abi,keyword,extended,,,Application Binary Interface (ABI) of the Linux OS.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.type,keyword,extended,,,Header type of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.header.version,keyword,extended,,,Version of the ELF header.
9.2.0-dev,true,threat,threat.indicator.file.elf.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in an ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.elf.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.elf.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections,nested,extended,array,,Section information of the ELF file.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.chi2,long,extended,,,Chi-square probability distribution of the section.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.flags,keyword,extended,,,ELF Section List flags.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.name,keyword,extended,,,ELF Section List name.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.physical_offset,keyword,extended,,,ELF Section List offset.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.physical_size,long,extended,,,ELF Section List physical size.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.type,keyword,extended,,,ELF Section List type.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.virtual_address,long,extended,,,ELF Section List virtual address.
9.2.0-dev,true,threat,threat.indicator.file.elf.sections.virtual_size,long,extended,,,ELF Section List virtual size.
9.2.0-dev,true,threat,threat.indicator.file.elf.segments,nested,extended,array,,ELF object segment list.
9.2.0-dev,true,threat,threat.indicator.file.elf.segments.sections,keyword,extended,,,ELF object segment sections.
9.2.0-dev,true,threat,threat.indicator.file.elf.segments.type,keyword,extended,,,ELF object segment type.
9.2.0-dev,true,threat,threat.indicator.file.elf.shared_libraries,keyword,extended,array,,List of shared libraries used by this ELF object.
9.2.0-dev,true,threat,threat.indicator.file.elf.telfhash,keyword,extended,,,telfhash hash for ELF file.
9.2.0-dev,true,threat,threat.indicator.file.extension,keyword,extended,,png,"File extension, excluding the leading dot."
9.2.0-dev,true,threat,threat.indicator.file.fork_name,keyword,extended,,Zone.Identifer,A fork is additional data associated with a filesystem object.
9.2.0-dev,true,threat,threat.indicator.file.gid,keyword,extended,,1001,Primary group ID (GID) of the file.
9.2.0-dev,true,threat,threat.indicator.file.group,keyword,extended,,alice,Primary group name of the file.
9.2.0-dev,true,threat,threat.indicator.file.hash.cdhash,keyword,extended,,3783b4052fd474dbe30676b45c329e7a6d44acd9,The Code Directory (CD) hash of an executable.
9.2.0-dev,true,threat,threat.indicator.file.hash.md5,keyword,extended,,,MD5 hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.sha1,keyword,extended,,,SHA1 hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.sha256,keyword,extended,,,SHA256 hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.sha384,keyword,extended,,,SHA384 hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.sha512,keyword,extended,,,SHA512 hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.ssdeep,keyword,extended,,,SSDEEP hash.
9.2.0-dev,true,threat,threat.indicator.file.hash.tlsh,keyword,extended,,,TLSH hash.
9.2.0-dev,true,threat,threat.indicator.file.inode,keyword,extended,,256383,Inode representing the file in the filesystem.
9.2.0-dev,true,threat,threat.indicator.file.mime_type,keyword,extended,,,"Media type of file, document, or arrangement of bytes."
9.2.0-dev,true,threat,threat.indicator.file.mode,keyword,extended,,0640,Mode of the file in octal representation.
9.2.0-dev,true,threat,threat.indicator.file.mtime,date,extended,,,Last time the file content was modified.
9.2.0-dev,true,threat,threat.indicator.file.name,keyword,extended,,example.png,"Name of the file including the extension, without the directory."
9.2.0-dev,true,threat,threat.indicator.file.origin_referrer_url,keyword,extended,,http://example.com/article1.html,The URL of the webpage that linked to the file.
9.2.0-dev,true,threat,threat.indicator.file.origin_url,keyword,extended,,http://example.com/imgs/article1_img1.jpg,The URL where the file is hosted.
9.2.0-dev,true,threat,threat.indicator.file.owner,keyword,extended,,alice,File owner's username.
9.2.0-dev,true,threat,threat.indicator.file.path,keyword,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,threat,threat.indicator.file.path.text,match_only_text,extended,,/home/alice/example.png,"Full path to the file, including the file name."
9.2.0-dev,true,threat,threat.indicator.file.pe.architecture,keyword,extended,,x64,CPU architecture target for the file.
9.2.0-dev,true,threat,threat.indicator.file.pe.company,keyword,extended,,Microsoft Corporation,"Internal company name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.indicator.file.pe.description,keyword,extended,,Paint,"Internal description of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.indicator.file.pe.file_version,keyword,extended,,6.3.9600.17415,Process name.
9.2.0-dev,true,threat,threat.indicator.file.pe.go_import_hash,keyword,extended,,10bddcb4cee42080f76c88d9ff964491,A hash of the Go language imports in a PE file.
9.2.0-dev,true,threat,threat.indicator.file.pe.go_imports,flattened,extended,,,List of imported Go language element names and types.
9.2.0-dev,true,threat,threat.indicator.file.pe.go_imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.indicator.file.pe.go_imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of Go imports.
9.2.0-dev,true,threat,threat.indicator.file.pe.go_stripped,boolean,extended,,,Whether the file is a stripped or obfuscated Go executable.
9.2.0-dev,true,threat,threat.indicator.file.pe.imphash,keyword,extended,,0c6803c4e922103c4dca5963aad36ddf,A hash of the imports in a PE file.
9.2.0-dev,true,threat,threat.indicator.file.pe.import_hash,keyword,extended,,d41d8cd98f00b204e9800998ecf8427e,A hash of the imports in a PE file.
9.2.0-dev,true,threat,threat.indicator.file.pe.imports,flattened,extended,array,,List of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.pe.imports_names_entropy,long,extended,,,Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.pe.imports_names_var_entropy,long,extended,,,Variance for Shannon entropy calculation from the list of imported element names and types.
9.2.0-dev,true,threat,threat.indicator.file.pe.original_file_name,keyword,extended,,MSPAINT.EXE,"Internal name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.indicator.file.pe.pehash,keyword,extended,,73ff189b63cd6be375a7ff25179a38d347651975,A hash of the PE header and data from one or more PE sections.
9.2.0-dev,true,threat,threat.indicator.file.pe.product,keyword,extended,,Microsoft® Windows® Operating System,"Internal product name of the file, provided at compile-time."
9.2.0-dev,true,threat,threat.indicator.file.pe.sections,nested,extended,array,,Section information of the PE file.
9.2.0-dev,true,threat,threat.indicator.file.pe.sections.entropy,long,extended,,,Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.indicator.file.pe.sections.name,keyword,extended,,,PE Section List name.
9.2.0-dev,true,threat,threat.indicator.file.pe.sections.physical_size,long,extended,,,PE Section List physical size.
9.2.0-dev,true,threat,threat.indicator.file.pe.sections.var_entropy,long,extended,,,Variance for Shannon entropy calculation from the section.
9.2.0-dev,true,threat,threat.indicator.file.pe.sections.virtual_size,long,extended,,,PE Section List virtual size. This is always the same as `physical_size`.
9.2.0-dev,true,threat,threat.indicator.file.size,long,extended,,16384,File size in bytes.
9.2.0-dev,true,threat,threat.indicator.file.target_path,keyword,extended,,,Target path for symlinks.
9.2.0-dev,true,threat,threat.indicator.file.target_path.text,match_only_text,extended,,,Target path for symlinks.
9.2.0-dev,true,threat,threat.indicator.file.type,keyword,extended,,file,"File type (file, dir, or symlink)."
9.2.0-dev,true,threat,threat.indicator.file.uid,keyword,extended,,1001,The user ID (UID) or security identifier (SID) of the file owner.
9.2.0-dev,true,threat,threat.indicator.file.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.file.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.indicator.file.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,threat,threat.indicator.file.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,threat,threat.indicator.file.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,threat,threat.indicator.file.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,threat,threat.indicator.file.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,threat,threat.indicator.file.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,threat,threat.indicator.file.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,threat,threat.indicator.file.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,threat,threat.indicator.file.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.indicator.file.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,threat,threat.indicator.first_seen,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was first reported.
9.2.0-dev,true,threat,threat.indicator.geo.city_name,keyword,core,,Montreal,City name.
9.2.0-dev,true,threat,threat.indicator.geo.continent_code,keyword,core,,NA,Continent code.
9.2.0-dev,true,threat,threat.indicator.geo.continent_name,keyword,core,,North America,Name of the continent.
9.2.0-dev,true,threat,threat.indicator.geo.country_iso_code,keyword,core,,CA,Country ISO code.
9.2.0-dev,true,threat,threat.indicator.geo.country_name,keyword,core,,Canada,Country name.
9.2.0-dev,true,threat,threat.indicator.geo.location,geo_point,core,,"{ ""lon"": -73.614830, ""lat"": 45.505918 }",Longitude and latitude.
9.2.0-dev,true,threat,threat.indicator.geo.name,keyword,extended,,boston-dc,User-defined description of a location.
9.2.0-dev,true,threat,threat.indicator.geo.postal_code,keyword,core,,94040,Postal code.
9.2.0-dev,true,threat,threat.indicator.geo.region_iso_code,keyword,core,,CA-QC,Region ISO code.
9.2.0-dev,true,threat,threat.indicator.geo.region_name,keyword,core,,Quebec,Region name.
9.2.0-dev,true,threat,threat.indicator.geo.timezone,keyword,core,,America/Argentina/Buenos_Aires,Time zone.
9.2.0-dev,true,threat,threat.indicator.id,keyword,extended,array,[indicator--d7008e06-ab86-415a-9803-3c81ce2d3c37],ID of the indicator
9.2.0-dev,true,threat,threat.indicator.ip,ip,extended,,1.2.3.4,Indicator IP address
9.2.0-dev,true,threat,threat.indicator.last_seen,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was last reported.
9.2.0-dev,true,threat,threat.indicator.marking.tlp,keyword,extended,,CLEAR,Indicator TLP marking
9.2.0-dev,true,threat,threat.indicator.marking.tlp_version,keyword,extended,,2.0,Indicator TLP version
9.2.0-dev,true,threat,threat.indicator.modified_at,date,extended,,2020-11-05T17:25:47.000Z,Date/time indicator was last updated.
9.2.0-dev,true,threat,threat.indicator.name,keyword,extended,,5.2.75.227,Indicator display name
9.2.0-dev,true,threat,threat.indicator.port,long,extended,,443,Indicator port
9.2.0-dev,true,threat,threat.indicator.provider,keyword,extended,,lrz_urlhaus,Indicator provider
9.2.0-dev,true,threat,threat.indicator.reference,keyword,extended,,https://system.example.com/indicator/0001234,Indicator reference URL
9.2.0-dev,true,threat,threat.indicator.registry.data.bytes,keyword,extended,,ZQBuAC0AVQBTAAAAZQBuAAAAAAA=,Original bytes written with base64 encoding.
9.2.0-dev,true,threat,threat.indicator.registry.data.strings,wildcard,core,array,"[""C:\rta\red_ttp\bin\myapp.exe""]",List of strings representing what was written to the registry.
9.2.0-dev,true,threat,threat.indicator.registry.data.type,keyword,core,,REG_SZ,Standard registry type for encoding contents
9.2.0-dev,true,threat,threat.indicator.registry.hive,keyword,core,,HKLM,Abbreviated name for the hive.
9.2.0-dev,true,threat,threat.indicator.registry.key,keyword,core,,SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe,Hive-relative path of keys.
9.2.0-dev,true,threat,threat.indicator.registry.path,keyword,core,,HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\winword.exe\Debugger,"Full path, including hive, key and value"
9.2.0-dev,true,threat,threat.indicator.registry.value,keyword,core,,Debugger,Name of the value written.
9.2.0-dev,true,threat,threat.indicator.scanner_stats,long,extended,,4,Scanner statistics
9.2.0-dev,true,threat,threat.indicator.sightings,long,extended,,20,Number of times indicator observed
9.2.0-dev,true,threat,threat.indicator.type,keyword,extended,,ipv4-addr,Type of indicator
9.2.0-dev,true,threat,threat.indicator.url.domain,keyword,extended,,www.elastic.co,Domain of the url.
9.2.0-dev,true,threat,threat.indicator.url.extension,keyword,extended,,png,"File extension from the request url, excluding the leading dot."
9.2.0-dev,true,threat,threat.indicator.url.fragment,keyword,extended,,,Portion of the url after the `#`.
9.2.0-dev,true,threat,threat.indicator.url.full,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,threat,threat.indicator.url.full.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,threat,threat.indicator.url.original,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,threat,threat.indicator.url.original.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,threat,threat.indicator.url.password,keyword,extended,,,Password of the request.
9.2.0-dev,true,threat,threat.indicator.url.path,wildcard,extended,,,"Path of the request, such as ""/search""."
9.2.0-dev,true,threat,threat.indicator.url.port,long,extended,,443,"Port of the request, such as 443."
9.2.0-dev,true,threat,threat.indicator.url.query,keyword,extended,,,Query string of the request.
9.2.0-dev,true,threat,threat.indicator.url.registered_domain,keyword,extended,,example.com,"The highest registered url domain, stripped of the subdomain."
9.2.0-dev,true,threat,threat.indicator.url.scheme,keyword,extended,,https,Scheme of the url.
9.2.0-dev,true,threat,threat.indicator.url.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,threat,threat.indicator.url.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,threat,threat.indicator.url.username,keyword,extended,,,Username of the request.
9.2.0-dev,true,threat,threat.indicator.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,threat,threat.indicator.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,threat,threat.indicator.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,threat,threat.indicator.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,threat,threat.indicator.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.indicator.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,threat,threat.indicator.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,threat,threat.indicator.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,threat,threat.indicator.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,threat,threat.indicator.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,threat,threat.indicator.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,threat,threat.indicator.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,threat,threat.indicator.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,threat,threat.indicator.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,threat,threat.indicator.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,threat,threat.indicator.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,threat,threat.indicator.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,threat,threat.indicator.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,threat,threat.indicator.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,threat,threat.indicator.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,threat,threat.indicator.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,threat,threat.software.alias,keyword,extended,array,"[ ""X-Agent"" ]",Alias of the software
9.2.0-dev,true,threat,threat.software.id,keyword,extended,,S0552,ID of the software
9.2.0-dev,true,threat,threat.software.name,keyword,extended,,AdFind,Name of the software.
9.2.0-dev,true,threat,threat.software.platforms,keyword,extended,array,"[ ""Windows"" ]",Platforms of the software.
9.2.0-dev,true,threat,threat.software.reference,keyword,extended,,https://attack.mitre.org/software/S0552/,Software reference URL.
9.2.0-dev,true,threat,threat.software.type,keyword,extended,,Tool,Software type.
9.2.0-dev,true,threat,threat.tactic.id,keyword,extended,array,TA0002,Threat tactic id.
9.2.0-dev,true,threat,threat.tactic.name,keyword,extended,array,Execution,Threat tactic.
9.2.0-dev,true,threat,threat.tactic.reference,keyword,extended,array,https://attack.mitre.org/tactics/TA0002/,Threat tactic URL reference.
9.2.0-dev,true,threat,threat.technique.id,keyword,extended,array,T1059,Threat technique id.
9.2.0-dev,true,threat,threat.technique.name,keyword,extended,array,Command and Scripting Interpreter,Threat technique name.
9.2.0-dev,true,threat,threat.technique.name.text,match_only_text,extended,,Command and Scripting Interpreter,Threat technique name.
9.2.0-dev,true,threat,threat.technique.reference,keyword,extended,array,https://attack.mitre.org/techniques/T1059/,Threat technique URL reference.
9.2.0-dev,true,threat,threat.technique.subtechnique.id,keyword,extended,array,T1059.001,Threat subtechnique id.
9.2.0-dev,true,threat,threat.technique.subtechnique.name,keyword,extended,array,PowerShell,Threat subtechnique name.
9.2.0-dev,true,threat,threat.technique.subtechnique.name.text,match_only_text,extended,,PowerShell,Threat subtechnique name.
9.2.0-dev,true,threat,threat.technique.subtechnique.reference,keyword,extended,array,https://attack.mitre.org/techniques/T1059/001/,Threat subtechnique URL reference.
9.2.0-dev,true,tls,tls.cipher,keyword,extended,,TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256,String indicating the cipher used during the current connection.
9.2.0-dev,true,tls,tls.client.certificate,keyword,extended,,MII...,PEM-encoded stand-alone certificate offered by the client.
9.2.0-dev,true,tls,tls.client.certificate_chain,keyword,extended,array,"[""MII..."", ""MII...""]",Array of PEM-encoded certificates that make up the certificate chain offered by the client.
9.2.0-dev,true,tls,tls.client.hash.md5,keyword,extended,,0F76C7F2C55BFD7D8E8B8F4BFBF0C9EC,Certificate fingerprint using the MD5 digest of DER-encoded version of certificate offered by the client.
9.2.0-dev,true,tls,tls.client.hash.sha1,keyword,extended,,9E393D93138888D288266C2D915214D1D1CCEB2A,Certificate fingerprint using the SHA1 digest of DER-encoded version of certificate offered by the client.
9.2.0-dev,true,tls,tls.client.hash.sha256,keyword,extended,,0687F666A054EF17A08E2F2162EAB4CBC0D265E1D7875BE74BF3C712CA92DAF0,Certificate fingerprint using the SHA256 digest of DER-encoded version of certificate offered by the client.
9.2.0-dev,true,tls,tls.client.issuer,keyword,extended,,"CN=Example Root CA, OU=Infrastructure Team, DC=example, DC=com",Distinguished name of subject of the issuer of the x.509 certificate presented by the client.
9.2.0-dev,true,tls,tls.client.ja3,keyword,extended,,d4e5b18d6b55c71272893221c96ba240,A hash that identifies clients based on how they perform an SSL/TLS handshake.
9.2.0-dev,true,tls,tls.client.not_after,date,extended,,2021-01-01T00:00:00.000Z,Date/Time indicating when client certificate is no longer considered valid.
9.2.0-dev,true,tls,tls.client.not_before,date,extended,,1970-01-01T00:00:00.000Z,Date/Time indicating when client certificate is first considered valid.
9.2.0-dev,true,tls,tls.client.server_name,keyword,extended,,www.elastic.co,Hostname the client is trying to connect to. Also called the SNI.
9.2.0-dev,true,tls,tls.client.subject,keyword,extended,,"CN=myclient, OU=Documentation Team, DC=example, DC=com",Distinguished name of subject of the x.509 certificate presented by the client.
9.2.0-dev,true,tls,tls.client.supported_ciphers,keyword,extended,array,"[""TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"", ""TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"", ""...""]",Array of ciphers offered by the client during the client hello.
9.2.0-dev,true,tls,tls.client.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,tls,tls.client.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,tls,tls.client.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,tls,tls.client.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,tls,tls.client.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,tls,tls.client.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,tls,tls.client.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,tls,tls.client.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,tls,tls.client.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,tls,tls.client.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,tls,tls.client.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,tls,tls.client.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,tls,tls.client.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,tls,tls.client.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,tls,tls.client.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,tls,tls.client.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,tls,tls.client.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,tls,tls.client.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,tls,tls.client.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,tls,tls.client.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,tls,tls.client.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,tls,tls.client.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,tls,tls.client.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,tls,tls.client.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,tls,tls.curve,keyword,extended,,secp256r1,"String indicating the curve used for the given cipher, when applicable."
9.2.0-dev,true,tls,tls.established,boolean,extended,,,Boolean flag indicating if the TLS negotiation was successful and transitioned to an encrypted tunnel.
9.2.0-dev,true,tls,tls.next_protocol,keyword,extended,,http/1.1,String indicating the protocol being tunneled.
9.2.0-dev,true,tls,tls.resumed,boolean,extended,,,Boolean flag indicating if this TLS connection was resumed from an existing TLS negotiation.
9.2.0-dev,true,tls,tls.server.certificate,keyword,extended,,MII...,PEM-encoded stand-alone certificate offered by the server.
9.2.0-dev,true,tls,tls.server.certificate_chain,keyword,extended,array,"[""MII..."", ""MII...""]",Array of PEM-encoded certificates that make up the certificate chain offered by the server.
9.2.0-dev,true,tls,tls.server.hash.md5,keyword,extended,,0F76C7F2C55BFD7D8E8B8F4BFBF0C9EC,Certificate fingerprint using the MD5 digest of DER-encoded version of certificate offered by the server.
9.2.0-dev,true,tls,tls.server.hash.sha1,keyword,extended,,9E393D93138888D288266C2D915214D1D1CCEB2A,Certificate fingerprint using the SHA1 digest of DER-encoded version of certificate offered by the server.
9.2.0-dev,true,tls,tls.server.hash.sha256,keyword,extended,,0687F666A054EF17A08E2F2162EAB4CBC0D265E1D7875BE74BF3C712CA92DAF0,Certificate fingerprint using the SHA256 digest of DER-encoded version of certificate offered by the server.
9.2.0-dev,true,tls,tls.server.issuer,keyword,extended,,"CN=Example Root CA, OU=Infrastructure Team, DC=example, DC=com",Subject of the issuer of the x.509 certificate presented by the server.
9.2.0-dev,true,tls,tls.server.ja3s,keyword,extended,,394441ab65754e2207b1e1b457b3641d,A hash that identifies servers based on how they perform an SSL/TLS handshake.
9.2.0-dev,true,tls,tls.server.not_after,date,extended,,2021-01-01T00:00:00.000Z,Timestamp indicating when server certificate is no longer considered valid.
9.2.0-dev,true,tls,tls.server.not_before,date,extended,,1970-01-01T00:00:00.000Z,Timestamp indicating when server certificate is first considered valid.
9.2.0-dev,true,tls,tls.server.subject,keyword,extended,,"CN=www.example.com, OU=Infrastructure Team, DC=example, DC=com",Subject of the x.509 certificate presented by the server.
9.2.0-dev,true,tls,tls.server.x509.alternative_names,keyword,extended,array,*.elastic.co,List of subject alternative names (SAN).
9.2.0-dev,true,tls,tls.server.x509.issuer.common_name,keyword,extended,array,Example SHA2 High Assurance Server CA,List of common name (CN) of issuing certificate authority.
9.2.0-dev,true,tls,tls.server.x509.issuer.country,keyword,extended,array,US,List of country \(C) codes
9.2.0-dev,true,tls,tls.server.x509.issuer.distinguished_name,keyword,extended,,"C=US, O=Example Inc, OU=www.example.com, CN=Example SHA2 High Assurance Server CA",Distinguished name (DN) of issuing certificate authority.
9.2.0-dev,true,tls,tls.server.x509.issuer.locality,keyword,extended,array,Mountain View,List of locality names (L)
9.2.0-dev,true,tls,tls.server.x509.issuer.organization,keyword,extended,array,Example Inc,List of organizations (O) of issuing certificate authority.
9.2.0-dev,true,tls,tls.server.x509.issuer.organizational_unit,keyword,extended,array,www.example.com,List of organizational units (OU) of issuing certificate authority.
9.2.0-dev,true,tls,tls.server.x509.issuer.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,tls,tls.server.x509.not_after,date,extended,,2020-07-16T03:15:39Z,Time at which the certificate is no longer considered valid.
9.2.0-dev,true,tls,tls.server.x509.not_before,date,extended,,2019-08-16T01:40:25Z,Time at which the certificate is first considered valid.
9.2.0-dev,true,tls,tls.server.x509.public_key_algorithm,keyword,extended,,RSA,Algorithm used to generate the public key.
9.2.0-dev,true,tls,tls.server.x509.public_key_curve,keyword,extended,,nistp521,The curve used by the elliptic curve public key algorithm. This is algorithm specific.
9.2.0-dev,false,tls,tls.server.x509.public_key_exponent,long,extended,,65537,Exponent used to derive the public key. This is algorithm specific.
9.2.0-dev,true,tls,tls.server.x509.public_key_size,long,extended,,2048,The size of the public key space in bits.
9.2.0-dev,true,tls,tls.server.x509.serial_number,keyword,extended,,55FBB9C7DEBF09809D12CCAA,Unique serial number issued by the certificate authority.
9.2.0-dev,true,tls,tls.server.x509.signature_algorithm,keyword,extended,,SHA256-RSA,Identifier for certificate signature algorithm.
9.2.0-dev,true,tls,tls.server.x509.subject.common_name,keyword,extended,array,shared.global.example.net,List of common names (CN) of subject.
9.2.0-dev,true,tls,tls.server.x509.subject.country,keyword,extended,array,US,List of country \(C) code
9.2.0-dev,true,tls,tls.server.x509.subject.distinguished_name,keyword,extended,,"C=US, ST=California, L=San Francisco, O=Example, Inc., CN=shared.global.example.net",Distinguished name (DN) of the certificate subject entity.
9.2.0-dev,true,tls,tls.server.x509.subject.locality,keyword,extended,array,San Francisco,List of locality names (L)
9.2.0-dev,true,tls,tls.server.x509.subject.organization,keyword,extended,array,"Example, Inc.",List of organizations (O) of subject.
9.2.0-dev,true,tls,tls.server.x509.subject.organizational_unit,keyword,extended,array,,List of organizational units (OU) of subject.
9.2.0-dev,true,tls,tls.server.x509.subject.state_or_province,keyword,extended,array,California,"List of state or province names (ST, S, or P)"
9.2.0-dev,true,tls,tls.server.x509.version_number,keyword,extended,,3,Version of x509 format.
9.2.0-dev,true,tls,tls.version,keyword,extended,,1.2,Numeric part of the version parsed from the original string.
9.2.0-dev,true,tls,tls.version_protocol,keyword,extended,,tls,Normalized lowercase protocol name parsed from original string.
9.2.0-dev,true,trace,trace.id,keyword,extended,,4bf92f3577b34da6a3ce929d0e0e4736,Unique identifier of the trace.
9.2.0-dev,true,transaction,transaction.id,keyword,extended,,00f067aa0ba902b7,Unique identifier of the transaction within the scope of its trace.
9.2.0-dev,true,url,url.domain,keyword,extended,,www.elastic.co,Domain of the url.
9.2.0-dev,true,url,url.extension,keyword,extended,,png,"File extension from the request url, excluding the leading dot."
9.2.0-dev,true,url,url.fragment,keyword,extended,,,Portion of the url after the `#`.
9.2.0-dev,true,url,url.full,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,url,url.full.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top,Full unparsed URL.
9.2.0-dev,true,url,url.original,wildcard,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,url,url.original.text,match_only_text,extended,,https://www.elastic.co:443/search?q=elasticsearch#top or /search?q=elasticsearch,Unmodified original url as seen in the event source.
9.2.0-dev,true,url,url.password,keyword,extended,,,Password of the request.
9.2.0-dev,true,url,url.path,wildcard,extended,,,"Path of the request, such as ""/search""."
9.2.0-dev,true,url,url.port,long,extended,,443,"Port of the request, such as 443."
9.2.0-dev,true,url,url.query,keyword,extended,,,Query string of the request.
9.2.0-dev,true,url,url.registered_domain,keyword,extended,,example.com,"The highest registered url domain, stripped of the subdomain."
9.2.0-dev,true,url,url.scheme,keyword,extended,,https,Scheme of the url.
9.2.0-dev,true,url,url.subdomain,keyword,extended,,east,The subdomain of the domain.
9.2.0-dev,true,url,url.top_level_domain,keyword,extended,,co.uk,"The effective top level domain (com, org, net, co.uk)."
9.2.0-dev,true,url,url.username,keyword,extended,,,Username of the request.
9.2.0-dev,true,user,user.changes.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,user,user.changes.email,keyword,extended,,,User email address.
9.2.0-dev,true,user,user.changes.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.changes.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.changes.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,user,user.changes.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,user,user.changes.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,user,user.changes.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,user,user.changes.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,user,user.changes.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.changes.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.changes.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,user,user.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,user,user.effective.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,user,user.effective.email,keyword,extended,,,User email address.
9.2.0-dev,true,user,user.effective.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.effective.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.effective.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,user,user.effective.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,user,user.effective.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,user,user.effective.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,user,user.effective.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,user,user.effective.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.effective.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.effective.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,user,user.email,keyword,extended,,,User email address.
9.2.0-dev,true,user,user.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,user,user.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,user,user.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,user,user.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,user,user.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,user,user.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.risk.calculated_level,keyword,extended,,High,A risk classification level calculated by an internal system as part of entity analytics and entity risk scoring.
9.2.0-dev,true,user,user.risk.calculated_score,float,extended,,880.73,A risk classification score calculated by an internal system as part of entity analytics and entity risk scoring.
9.2.0-dev,true,user,user.risk.calculated_score_norm,float,extended,,88.73,A normalized risk score calculated by an internal system.
9.2.0-dev,true,user,user.risk.static_level,keyword,extended,,High,"A risk classification level obtained from outside the system, such as from some external Threat Intelligence Platform."
9.2.0-dev,true,user,user.risk.static_score,float,extended,,830.0,"A risk classification score obtained from outside the system, such as from some external Threat Intelligence Platform."
9.2.0-dev,true,user,user.risk.static_score_norm,float,extended,,83.0,A normalized risk score calculated by an external system.
9.2.0-dev,true,user,user.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,user,user.target.domain,keyword,extended,,,Name of the directory the user is a member of.
9.2.0-dev,true,user,user.target.email,keyword,extended,,,User email address.
9.2.0-dev,true,user,user.target.full_name,keyword,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.target.full_name.text,match_only_text,extended,,Albert Einstein,"User's full name, if available."
9.2.0-dev,true,user,user.target.group.domain,keyword,extended,,,Name of the directory the group is a member of.
9.2.0-dev,true,user,user.target.group.id,keyword,extended,,,Unique identifier for the group on the system/platform.
9.2.0-dev,true,user,user.target.group.name,keyword,extended,,,Name of the group.
9.2.0-dev,true,user,user.target.hash,keyword,extended,,,Unique user hash to correlate information for a user in anonymized form.
9.2.0-dev,true,user,user.target.id,keyword,core,,S-1-5-21-202424912787-2692429404-2351956786-1000,Unique identifier of the user.
9.2.0-dev,true,user,user.target.name,keyword,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.target.name.text,match_only_text,core,,a.einstein,Short name or login of the user.
9.2.0-dev,true,user,user.target.roles,keyword,extended,array,"[""kibana_admin"", ""reporting_user""]",Array of user roles at the time of the event.
9.2.0-dev,true,user_agent,user_agent.device.name,keyword,extended,,iPhone,Name of the device.
9.2.0-dev,true,user_agent,user_agent.name,keyword,extended,,Safari,Name of the user agent.
9.2.0-dev,true,user_agent,user_agent.original,keyword,extended,,"Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",Unparsed user_agent string.
9.2.0-dev,true,user_agent,user_agent.original.text,match_only_text,extended,,"Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",Unparsed user_agent string.
9.2.0-dev,true,user_agent,user_agent.os.family,keyword,extended,,debian,"OS family (such as redhat, debian, freebsd, windows)."
9.2.0-dev,true,user_agent,user_agent.os.full,keyword,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,user_agent,user_agent.os.full.text,match_only_text,extended,,Mac OS Mojave,"Operating system name, including the version or code name."
9.2.0-dev,true,user_agent,user_agent.os.kernel,keyword,extended,,4.4.0-112-generic,Operating system kernel version as a raw string.
9.2.0-dev,true,user_agent,user_agent.os.name,keyword,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,user_agent,user_agent.os.name.text,match_only_text,extended,,Mac OS X,"Operating system name, without the version."
9.2.0-dev,true,user_agent,user_agent.os.platform,keyword,extended,,darwin,"Operating system platform (such centos, ubuntu, windows)."
9.2.0-dev,true,user_agent,user_agent.os.type,keyword,extended,,macos,"Which commercial OS family (one of: linux, macos, unix, windows, ios or android)."
9.2.0-dev,true,user_agent,user_agent.os.version,keyword,extended,,10.14.1,Operating system version as a raw string.
9.2.0-dev,true,user_agent,user_agent.version,keyword,extended,,12.0,Version of the user agent.
9.2.0-dev,true,volume,volume.bus_type,keyword,extended,,FileBackedVirtual,Bus type of the device.
9.2.0-dev,true,volume,volume.default_access,keyword,extended,,,Bus type of the device.
9.2.0-dev,true,volume,volume.device_name,keyword,extended,,,Device name of the volume.
9.2.0-dev,true,volume,volume.device_type,keyword,extended,,CD-ROM File System,Volume device type.
9.2.0-dev,true,volume,volume.dos_name,keyword,extended,,E:,DOS name of the device.
9.2.0-dev,true,volume,volume.file_system_type,keyword,extended,,,Volume device file system type.
9.2.0-dev,true,volume,volume.mount_name,keyword,extended,,,Mount name of the volume.
9.2.0-dev,true,volume,volume.nt_name,keyword,extended,,\Device\Cdrom1,NT name of the device.
9.2.0-dev,true,volume,volume.product_id,keyword,extended,,,ProductID of the device.
9.2.0-dev,true,volume,volume.product_name,keyword,extended,,Virtual DVD-ROM,Produce name of the volume.
9.2.0-dev,true,volume,volume.removable,boolean,extended,,,Indicates if the volume is removable.
9.2.0-dev,true,volume,volume.serial_number,keyword,extended,,,Serial number of the device.
9.2.0-dev,true,volume,volume.size,long,extended,,,Size of the volume device in bytes.
9.2.0-dev,true,volume,volume.vendor_id,keyword,extended,,,VendorID of the device.
9.2.0-dev,true,volume,volume.vendor_name,keyword,extended,,Msft,Vendor name of the device.
9.2.0-dev,true,volume,volume.writable,boolean,extended,,,Indicates if the volume is writable.
9.2.0-dev,true,vulnerability,vulnerability.category,keyword,extended,array,"[""Firewall""]",Category of a vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.classification,keyword,extended,,CVSS,Classification of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.description,keyword,extended,,"In macOS before 2.12.6, there is a vulnerability in the RPC...",Description of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.description.text,match_only_text,extended,,"In macOS before 2.12.6, there is a vulnerability in the RPC...",Description of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.enumeration,keyword,extended,,CVE,Identifier of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.id,keyword,extended,,CVE-2019-00001,ID of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.reference,keyword,extended,,https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-6111,Reference of the vulnerability.
9.2.0-dev,true,vulnerability,vulnerability.report_id,keyword,extended,,20191018.0001,Scan identification number.
9.2.0-dev,true,vulnerability,vulnerability.scanner.vendor,keyword,extended,,Tenable,Name of the scanner vendor.
9.2.0-dev,true,vulnerability,vulnerability.score.base,float,extended,,5.5,Vulnerability Base score.
9.2.0-dev,true,vulnerability,vulnerability.score.environmental,float,extended,,5.5,Vulnerability Environmental score.
9.2.0-dev,true,vulnerability,vulnerability.score.temporal,float,extended,,,Vulnerability Temporal score.
9.2.0-dev,true,vulnerability,vulnerability.score.version,keyword,extended,,2.0,CVSS version.
9.2.0-dev,true,vulnerability,vulnerability.severity,keyword,extended,,Critical,Severity of the vulnerability.
ENDMSG
```
---
### rag/elastic_logtypes.csv
```bash
cat > "/opt/SmartSOC/web/rag/elastic_logtypes.csv" <<"ENDMSG"
Package,Logtype,Documentation_URL
1password,1password,https://github.com/elastic/integrations/tree/main/packages/1password
abnormal_security,abnormal_security,https://github.com/elastic/integrations/tree/main/packages/abnormal_security
activemq,activemq,https://github.com/elastic/integrations/tree/main/packages/activemq
admin_by_request_epm,admin_by_request_epm,https://github.com/elastic/integrations/tree/main/packages/admin_by_request_epm
airflow,airflow,https://github.com/elastic/integrations/tree/main/packages/airflow
akamai,akamai,https://github.com/elastic/integrations/tree/main/packages/akamai
amazon_security_lake,amazon_security_lake,https://github.com/elastic/integrations/tree/main/packages/amazon_security_lake
apache,apache,https://github.com/elastic/integrations/tree/main/packages/apache
apache_spark,apache_spark,https://github.com/elastic/integrations/tree/main/packages/apache_spark
apache_tomcat,apache_tomcat,https://github.com/elastic/integrations/tree/main/packages/apache_tomcat
apm,apm,https://github.com/elastic/integrations/tree/main/packages/apm
arista_ngfw,arista_ngfw,https://github.com/elastic/integrations/tree/main/packages/arista_ngfw
armis,armis,https://github.com/elastic/integrations/tree/main/packages/armis
atlassian_bitbucket,atlassian_bitbucket,https://github.com/elastic/integrations/tree/main/packages/atlassian_bitbucket
atlassian_confluence,atlassian_confluence,https://github.com/elastic/integrations/tree/main/packages/atlassian_confluence
atlassian_jira,atlassian_jira,https://github.com/elastic/integrations/tree/main/packages/atlassian_jira
auditd,auditd,https://github.com/elastic/integrations/tree/main/packages/auditd
auditd_manager,auditd_manager,https://github.com/elastic/integrations/tree/main/packages/auditd_manager
auth0,auth0,https://github.com/elastic/integrations/tree/main/packages/auth0
authentik,authentik,https://github.com/elastic/integrations/tree/main/packages/authentik
aws,aws,https://github.com/elastic/integrations/tree/main/packages/aws
awsfargate,awsfargate,https://github.com/elastic/integrations/tree/main/packages/awsfargate
awsfirehose,awsfirehose,https://github.com/elastic/integrations/tree/main/packages/awsfirehose
aws_bedrock,aws_bedrock,https://github.com/elastic/integrations/tree/main/packages/aws_bedrock
aws_logs,aws_logs,https://github.com/elastic/integrations/tree/main/packages/aws_logs
aws_mq,aws_mq,https://github.com/elastic/integrations/tree/main/packages/aws_mq
azure,azure,https://github.com/elastic/integrations/tree/main/packages/azure
azure_application_insights,azure_application_insights,https://github.com/elastic/integrations/tree/main/packages/azure_application_insights
azure_app_service,azure_app_service,https://github.com/elastic/integrations/tree/main/packages/azure_app_service
azure_billing,azure_billing,https://github.com/elastic/integrations/tree/main/packages/azure_billing
azure_blob_storage,azure_blob_storage,https://github.com/elastic/integrations/tree/main/packages/azure_blob_storage
azure_frontdoor,azure_frontdoor,https://github.com/elastic/integrations/tree/main/packages/azure_frontdoor
azure_functions,azure_functions,https://github.com/elastic/integrations/tree/main/packages/azure_functions
azure_logs,azure_logs,https://github.com/elastic/integrations/tree/main/packages/azure_logs
azure_metrics,azure_metrics,https://github.com/elastic/integrations/tree/main/packages/azure_metrics
azure_network_watcher_nsg,azure_network_watcher_nsg,https://github.com/elastic/integrations/tree/main/packages/azure_network_watcher_nsg
azure_network_watcher_vnet,azure_network_watcher_vnet,https://github.com/elastic/integrations/tree/main/packages/azure_network_watcher_vnet
azure_openai,azure_openai,https://github.com/elastic/integrations/tree/main/packages/azure_openai
barracuda,barracuda,https://github.com/elastic/integrations/tree/main/packages/barracuda
barracuda_cloudgen_firewall,barracuda_cloudgen_firewall,https://github.com/elastic/integrations/tree/main/packages/barracuda_cloudgen_firewall
bbot,bbot,https://github.com/elastic/integrations/tree/main/packages/bbot
beaconing,beaconing,https://github.com/elastic/integrations/tree/main/packages/beaconing
beat,beat,https://github.com/elastic/integrations/tree/main/packages/beat
beelzebub,beelzebub,https://github.com/elastic/integrations/tree/main/packages/beelzebub
beyondinsight_password_safe,beyondinsight_password_safe,https://github.com/elastic/integrations/tree/main/packages/beyondinsight_password_safe
beyondtrust_pra,beyondtrust_pra,https://github.com/elastic/integrations/tree/main/packages/beyondtrust_pra
bitdefender,bitdefender,https://github.com/elastic/integrations/tree/main/packages/bitdefender
bitwarden,bitwarden,https://github.com/elastic/integrations/tree/main/packages/bitwarden
blacklens,blacklens,https://github.com/elastic/integrations/tree/main/packages/blacklens
bluecoat,bluecoat,https://github.com/elastic/integrations/tree/main/packages/bluecoat
box_events,box_events,https://github.com/elastic/integrations/tree/main/packages/box_events
canva,canva,https://github.com/elastic/integrations/tree/main/packages/canva
carbonblack_edr,carbonblack_edr,https://github.com/elastic/integrations/tree/main/packages/carbonblack_edr
carbon_black_cloud,carbon_black_cloud,https://github.com/elastic/integrations/tree/main/packages/carbon_black_cloud
cassandra,cassandra,https://github.com/elastic/integrations/tree/main/packages/cassandra
cef,cef,https://github.com/elastic/integrations/tree/main/packages/cef
cel,cel,https://github.com/elastic/integrations/tree/main/packages/cel
ceph,ceph,https://github.com/elastic/integrations/tree/main/packages/ceph
checkpoint,checkpoint,https://github.com/elastic/integrations/tree/main/packages/checkpoint
checkpoint_email,checkpoint_email,https://github.com/elastic/integrations/tree/main/packages/checkpoint_email
checkpoint_harmony_endpoint,checkpoint_harmony_endpoint,https://github.com/elastic/integrations/tree/main/packages/checkpoint_harmony_endpoint
cisa_kevs,cisa_kevs,https://github.com/elastic/integrations/tree/main/packages/cisa_kevs
cisco_aironet,cisco_aironet,https://github.com/elastic/integrations/tree/main/packages/cisco_aironet
cisco_asa,cisco_asa,https://github.com/elastic/integrations/tree/main/packages/cisco_asa
cisco_duo,cisco_duo,https://github.com/elastic/integrations/tree/main/packages/cisco_duo
cisco_ftd,cisco_ftd,https://github.com/elastic/integrations/tree/main/packages/cisco_ftd
cisco_ios,cisco_ios,https://github.com/elastic/integrations/tree/main/packages/cisco_ios
cisco_ise,cisco_ise,https://github.com/elastic/integrations/tree/main/packages/cisco_ise
cisco_meraki,cisco_meraki,https://github.com/elastic/integrations/tree/main/packages/cisco_meraki
cisco_meraki_metrics,cisco_meraki_metrics,https://github.com/elastic/integrations/tree/main/packages/cisco_meraki_metrics
cisco_nexus,cisco_nexus,https://github.com/elastic/integrations/tree/main/packages/cisco_nexus
cisco_secure_email_gateway,cisco_secure_email_gateway,https://github.com/elastic/integrations/tree/main/packages/cisco_secure_email_gateway
cisco_secure_endpoint,cisco_secure_endpoint,https://github.com/elastic/integrations/tree/main/packages/cisco_secure_endpoint
cisco_umbrella,cisco_umbrella,https://github.com/elastic/integrations/tree/main/packages/cisco_umbrella
citrix_adc,citrix_adc,https://github.com/elastic/integrations/tree/main/packages/citrix_adc
citrix_waf,citrix_waf,https://github.com/elastic/integrations/tree/main/packages/citrix_waf
claroty_ctd,claroty_ctd,https://github.com/elastic/integrations/tree/main/packages/claroty_ctd
claroty_xdome,claroty_xdome,https://github.com/elastic/integrations/tree/main/packages/claroty_xdome
cloudflare,cloudflare,https://github.com/elastic/integrations/tree/main/packages/cloudflare
cloudflare_logpush,cloudflare_logpush,https://github.com/elastic/integrations/tree/main/packages/cloudflare_logpush
cloud_asset_inventory,cloud_asset_inventory,https://github.com/elastic/integrations/tree/main/packages/cloud_asset_inventory
cloud_defend,cloud_defend,https://github.com/elastic/integrations/tree/main/packages/cloud_defend
cloud_security_posture,cloud_security_posture,https://github.com/elastic/integrations/tree/main/packages/cloud_security_posture
cockroachdb,cockroachdb,https://github.com/elastic/integrations/tree/main/packages/cockroachdb
containerd,containerd,https://github.com/elastic/integrations/tree/main/packages/containerd
coredns,coredns,https://github.com/elastic/integrations/tree/main/packages/coredns
corelight,corelight,https://github.com/elastic/integrations/tree/main/packages/corelight
couchbase,couchbase,https://github.com/elastic/integrations/tree/main/packages/couchbase
couchdb,couchdb,https://github.com/elastic/integrations/tree/main/packages/couchdb
cribl,cribl,https://github.com/elastic/integrations/tree/main/packages/cribl
crowdstrike,crowdstrike,https://github.com/elastic/integrations/tree/main/packages/crowdstrike
cyberarkpas,cyberarkpas,https://github.com/elastic/integrations/tree/main/packages/cyberarkpas
cyberark_epm,cyberark_epm,https://github.com/elastic/integrations/tree/main/packages/cyberark_epm
cyberark_pta,cyberark_pta,https://github.com/elastic/integrations/tree/main/packages/cyberark_pta
cybereason,cybereason,https://github.com/elastic/integrations/tree/main/packages/cybereason
cylance,cylance,https://github.com/elastic/integrations/tree/main/packages/cylance
darktrace,darktrace,https://github.com/elastic/integrations/tree/main/packages/darktrace
ded,ded,https://github.com/elastic/integrations/tree/main/packages/ded
dga,dga,https://github.com/elastic/integrations/tree/main/packages/dga
digital_guardian,digital_guardian,https://github.com/elastic/integrations/tree/main/packages/digital_guardian
docker,docker,https://github.com/elastic/integrations/tree/main/packages/docker
docker_otel,docker_otel,https://github.com/elastic/integrations/tree/main/packages/docker_otel
elasticsearch,elasticsearch,https://github.com/elastic/integrations/tree/main/packages/elasticsearch
elastic_agent,elastic_agent,https://github.com/elastic/integrations/tree/main/packages/elastic_agent
elastic_connectors,elastic_connectors,https://github.com/elastic/integrations/tree/main/packages/elastic_connectors
elastic_package_registry,elastic_package_registry,https://github.com/elastic/integrations/tree/main/packages/elastic_package_registry
endace,endace,https://github.com/elastic/integrations/tree/main/packages/endace
enterprisesearch,enterprisesearch,https://github.com/elastic/integrations/tree/main/packages/enterprisesearch
entityanalytics_ad,entityanalytics_ad,https://github.com/elastic/integrations/tree/main/packages/entityanalytics_ad
entityanalytics_entra_id,entityanalytics_entra_id,https://github.com/elastic/integrations/tree/main/packages/entityanalytics_entra_id
entityanalytics_okta,entityanalytics_okta,https://github.com/elastic/integrations/tree/main/packages/entityanalytics_okta
envoyproxy,envoyproxy,https://github.com/elastic/integrations/tree/main/packages/envoyproxy
eset_protect,eset_protect,https://github.com/elastic/integrations/tree/main/packages/eset_protect
ess_billing,ess_billing,https://github.com/elastic/integrations/tree/main/packages/ess_billing
etcd,etcd,https://github.com/elastic/integrations/tree/main/packages/etcd
f5_bigip,f5_bigip,https://github.com/elastic/integrations/tree/main/packages/f5_bigip
falco,falco,https://github.com/elastic/integrations/tree/main/packages/falco
filestream,filestream,https://github.com/elastic/integrations/tree/main/packages/filestream
fim,fim,https://github.com/elastic/integrations/tree/main/packages/fim
fireeye,fireeye,https://github.com/elastic/integrations/tree/main/packages/fireeye
first_epss,first_epss,https://github.com/elastic/integrations/tree/main/packages/first_epss
fleet_server,fleet_server,https://github.com/elastic/integrations/tree/main/packages/fleet_server
forcepoint_web,forcepoint_web,https://github.com/elastic/integrations/tree/main/packages/forcepoint_web
forgerock,forgerock,https://github.com/elastic/integrations/tree/main/packages/forgerock
fortinet_forticlient,fortinet_forticlient,https://github.com/elastic/integrations/tree/main/packages/fortinet_forticlient
fortinet_fortiedr,fortinet_fortiedr,https://github.com/elastic/integrations/tree/main/packages/fortinet_fortiedr
fortinet_fortigate,fortinet_fortigate,https://github.com/elastic/integrations/tree/main/packages/fortinet_fortigate
fortinet_fortimail,fortinet_fortimail,https://github.com/elastic/integrations/tree/main/packages/fortinet_fortimail
fortinet_fortimanager,fortinet_fortimanager,https://github.com/elastic/integrations/tree/main/packages/fortinet_fortimanager
fortinet_fortiproxy,fortinet_fortiproxy,https://github.com/elastic/integrations/tree/main/packages/fortinet_fortiproxy
gcp,gcp,https://github.com/elastic/integrations/tree/main/packages/gcp
gcp_metrics,gcp_metrics,https://github.com/elastic/integrations/tree/main/packages/gcp_metrics
gcp_pubsub,gcp_pubsub,https://github.com/elastic/integrations/tree/main/packages/gcp_pubsub
gcp_vertexai,gcp_vertexai,https://github.com/elastic/integrations/tree/main/packages/gcp_vertexai
gigamon,gigamon,https://github.com/elastic/integrations/tree/main/packages/gigamon
github,github,https://github.com/elastic/integrations/tree/main/packages/github
gitlab,gitlab,https://github.com/elastic/integrations/tree/main/packages/gitlab
goflow2,goflow2,https://github.com/elastic/integrations/tree/main/packages/goflow2
golang,golang,https://github.com/elastic/integrations/tree/main/packages/golang
google_cloud_storage,google_cloud_storage,https://github.com/elastic/integrations/tree/main/packages/google_cloud_storage
google_scc,google_scc,https://github.com/elastic/integrations/tree/main/packages/google_scc
google_secops,google_secops,https://github.com/elastic/integrations/tree/main/packages/google_secops
google_workspace,google_workspace,https://github.com/elastic/integrations/tree/main/packages/google_workspace
hadoop,hadoop,https://github.com/elastic/integrations/tree/main/packages/hadoop
haproxy,haproxy,https://github.com/elastic/integrations/tree/main/packages/haproxy
hashicorp_vault,hashicorp_vault,https://github.com/elastic/integrations/tree/main/packages/hashicorp_vault
hid_bravura_monitor,hid_bravura_monitor,https://github.com/elastic/integrations/tree/main/packages/hid_bravura_monitor
hpe_aruba_cx,hpe_aruba_cx,https://github.com/elastic/integrations/tree/main/packages/hpe_aruba_cx
hta,hta,https://github.com/elastic/integrations/tree/main/packages/hta
httpjson,httpjson,https://github.com/elastic/integrations/tree/main/packages/httpjson
http_endpoint,http_endpoint,https://github.com/elastic/integrations/tree/main/packages/http_endpoint
ibmmq,ibmmq,https://github.com/elastic/integrations/tree/main/packages/ibmmq
iis,iis,https://github.com/elastic/integrations/tree/main/packages/iis
imperva,imperva,https://github.com/elastic/integrations/tree/main/packages/imperva
imperva_cloud_waf,imperva_cloud_waf,https://github.com/elastic/integrations/tree/main/packages/imperva_cloud_waf
influxdb,influxdb,https://github.com/elastic/integrations/tree/main/packages/influxdb
infoblox_bloxone_ddi,infoblox_bloxone_ddi,https://github.com/elastic/integrations/tree/main/packages/infoblox_bloxone_ddi
infoblox_nios,infoblox_nios,https://github.com/elastic/integrations/tree/main/packages/infoblox_nios
iptables,iptables,https://github.com/elastic/integrations/tree/main/packages/iptables
istio,istio,https://github.com/elastic/integrations/tree/main/packages/istio
jamf_compliance_reporter,jamf_compliance_reporter,https://github.com/elastic/integrations/tree/main/packages/jamf_compliance_reporter
jamf_pro,jamf_pro,https://github.com/elastic/integrations/tree/main/packages/jamf_pro
jamf_protect,jamf_protect,https://github.com/elastic/integrations/tree/main/packages/jamf_protect
jolokia_input,jolokia_input,https://github.com/elastic/integrations/tree/main/packages/jolokia_input
journald,journald,https://github.com/elastic/integrations/tree/main/packages/journald
jumpcloud,jumpcloud,https://github.com/elastic/integrations/tree/main/packages/jumpcloud
juniper_junos,juniper_junos,https://github.com/elastic/integrations/tree/main/packages/juniper_junos
juniper_netscreen,juniper_netscreen,https://github.com/elastic/integrations/tree/main/packages/juniper_netscreen
juniper_srx,juniper_srx,https://github.com/elastic/integrations/tree/main/packages/juniper_srx
kafka,kafka,https://github.com/elastic/integrations/tree/main/packages/kafka
kafka_log,kafka_log,https://github.com/elastic/integrations/tree/main/packages/kafka_log
keycloak,keycloak,https://github.com/elastic/integrations/tree/main/packages/keycloak
kibana,kibana,https://github.com/elastic/integrations/tree/main/packages/kibana
kubernetes,kubernetes,https://github.com/elastic/integrations/tree/main/packages/kubernetes
kubernetes_otel,kubernetes_otel,https://github.com/elastic/integrations/tree/main/packages/kubernetes_otel
lastpass,lastpass,https://github.com/elastic/integrations/tree/main/packages/lastpass
linux,linux,https://github.com/elastic/integrations/tree/main/packages/linux
lmd,lmd,https://github.com/elastic/integrations/tree/main/packages/lmd
log,log,https://github.com/elastic/integrations/tree/main/packages/log
logstash,logstash,https://github.com/elastic/integrations/tree/main/packages/logstash
lumos,lumos,https://github.com/elastic/integrations/tree/main/packages/lumos
lyve_cloud,lyve_cloud,https://github.com/elastic/integrations/tree/main/packages/lyve_cloud
m365_defender,m365_defender,https://github.com/elastic/integrations/tree/main/packages/m365_defender
mattermost,mattermost,https://github.com/elastic/integrations/tree/main/packages/mattermost
memcached,memcached,https://github.com/elastic/integrations/tree/main/packages/memcached
menlo,menlo,https://github.com/elastic/integrations/tree/main/packages/menlo
microsoft_defender_cloud,microsoft_defender_cloud,https://github.com/elastic/integrations/tree/main/packages/microsoft_defender_cloud
microsoft_defender_endpoint,microsoft_defender_endpoint,https://github.com/elastic/integrations/tree/main/packages/microsoft_defender_endpoint
microsoft_dhcp,microsoft_dhcp,https://github.com/elastic/integrations/tree/main/packages/microsoft_dhcp
microsoft_dnsserver,microsoft_dnsserver,https://github.com/elastic/integrations/tree/main/packages/microsoft_dnsserver
microsoft_exchange_online_message_trace,microsoft_exchange_online_message_trace,https://github.com/elastic/integrations/tree/main/packages/microsoft_exchange_online_message_trace
microsoft_exchange_server,microsoft_exchange_server,https://github.com/elastic/integrations/tree/main/packages/microsoft_exchange_server
microsoft_sentinel,microsoft_sentinel,https://github.com/elastic/integrations/tree/main/packages/microsoft_sentinel
microsoft_sqlserver,microsoft_sqlserver,https://github.com/elastic/integrations/tree/main/packages/microsoft_sqlserver
mimecast,mimecast,https://github.com/elastic/integrations/tree/main/packages/mimecast
miniflux,miniflux,https://github.com/elastic/integrations/tree/main/packages/miniflux
modsecurity,modsecurity,https://github.com/elastic/integrations/tree/main/packages/modsecurity
mongodb,mongodb,https://github.com/elastic/integrations/tree/main/packages/mongodb
mongodb_atlas,mongodb_atlas,https://github.com/elastic/integrations/tree/main/packages/mongodb_atlas
mysql,mysql,https://github.com/elastic/integrations/tree/main/packages/mysql
mysql_enterprise,mysql_enterprise,https://github.com/elastic/integrations/tree/main/packages/mysql_enterprise
nagios_xi,nagios_xi,https://github.com/elastic/integrations/tree/main/packages/nagios_xi
nats,nats,https://github.com/elastic/integrations/tree/main/packages/nats
netflow,netflow,https://github.com/elastic/integrations/tree/main/packages/netflow
netscout,netscout,https://github.com/elastic/integrations/tree/main/packages/netscout
netskope,netskope,https://github.com/elastic/integrations/tree/main/packages/netskope
network_traffic,network_traffic,https://github.com/elastic/integrations/tree/main/packages/network_traffic
nginx,nginx,https://github.com/elastic/integrations/tree/main/packages/nginx
nginx_ingress_controller,nginx_ingress_controller,https://github.com/elastic/integrations/tree/main/packages/nginx_ingress_controller
nginx_ingress_controller_otel,nginx_ingress_controller_otel,https://github.com/elastic/integrations/tree/main/packages/nginx_ingress_controller_otel
nvidia_gpu,nvidia_gpu,https://github.com/elastic/integrations/tree/main/packages/nvidia_gpu
o365,o365,https://github.com/elastic/integrations/tree/main/packages/o365
o365_metrics,o365_metrics,https://github.com/elastic/integrations/tree/main/packages/o365_metrics
okta,okta,https://github.com/elastic/integrations/tree/main/packages/okta
openai,openai,https://github.com/elastic/integrations/tree/main/packages/openai
opencanary,opencanary,https://github.com/elastic/integrations/tree/main/packages/opencanary
oracle,oracle,https://github.com/elastic/integrations/tree/main/packages/oracle
oracle_weblogic,oracle_weblogic,https://github.com/elastic/integrations/tree/main/packages/oracle_weblogic
osquery,osquery,https://github.com/elastic/integrations/tree/main/packages/osquery
osquery_manager,osquery_manager,https://github.com/elastic/integrations/tree/main/packages/osquery_manager
pad,pad,https://github.com/elastic/integrations/tree/main/packages/pad
panw,panw,https://github.com/elastic/integrations/tree/main/packages/panw
panw_cortex_xdr,panw_cortex_xdr,https://github.com/elastic/integrations/tree/main/packages/panw_cortex_xdr
panw_metrics,panw_metrics,https://github.com/elastic/integrations/tree/main/packages/panw_metrics
pfsense,pfsense,https://github.com/elastic/integrations/tree/main/packages/pfsense
php_fpm,php_fpm,https://github.com/elastic/integrations/tree/main/packages/php_fpm
ping_federate,ping_federate,https://github.com/elastic/integrations/tree/main/packages/ping_federate
ping_one,ping_one,https://github.com/elastic/integrations/tree/main/packages/ping_one
platform_observability,platform_observability,https://github.com/elastic/integrations/tree/main/packages/platform_observability
postgresql,postgresql,https://github.com/elastic/integrations/tree/main/packages/postgresql
pps,pps,https://github.com/elastic/integrations/tree/main/packages/pps
prisma_access,prisma_access,https://github.com/elastic/integrations/tree/main/packages/prisma_access
prisma_cloud,prisma_cloud,https://github.com/elastic/integrations/tree/main/packages/prisma_cloud
problemchild,problemchild,https://github.com/elastic/integrations/tree/main/packages/problemchild
prometheus,prometheus,https://github.com/elastic/integrations/tree/main/packages/prometheus
prometheus_input,prometheus_input,https://github.com/elastic/integrations/tree/main/packages/prometheus_input
proofpoint_itm,proofpoint_itm,https://github.com/elastic/integrations/tree/main/packages/proofpoint_itm
proofpoint_on_demand,proofpoint_on_demand,https://github.com/elastic/integrations/tree/main/packages/proofpoint_on_demand
proofpoint_tap,proofpoint_tap,https://github.com/elastic/integrations/tree/main/packages/proofpoint_tap
proxysg,proxysg,https://github.com/elastic/integrations/tree/main/packages/proxysg
pulse_connect_secure,pulse_connect_secure,https://github.com/elastic/integrations/tree/main/packages/pulse_connect_secure
qnap_nas,qnap_nas,https://github.com/elastic/integrations/tree/main/packages/qnap_nas
qualys_vmdr,qualys_vmdr,https://github.com/elastic/integrations/tree/main/packages/qualys_vmdr
rabbitmq,rabbitmq,https://github.com/elastic/integrations/tree/main/packages/rabbitmq
radware,radware,https://github.com/elastic/integrations/tree/main/packages/radware
rapid7_insightvm,rapid7_insightvm,https://github.com/elastic/integrations/tree/main/packages/rapid7_insightvm
redis,redis,https://github.com/elastic/integrations/tree/main/packages/redis
redisenterprise,redisenterprise,https://github.com/elastic/integrations/tree/main/packages/redisenterprise
rubrik,rubrik,https://github.com/elastic/integrations/tree/main/packages/rubrik
sailpoint_identity_sc,sailpoint_identity_sc,https://github.com/elastic/integrations/tree/main/packages/sailpoint_identity_sc
salesforce,salesforce,https://github.com/elastic/integrations/tree/main/packages/salesforce
santa,santa,https://github.com/elastic/integrations/tree/main/packages/santa
security_ai_prompts,security_ai_prompts,https://github.com/elastic/integrations/tree/main/packages/security_ai_prompts
security_detection_engine,security_detection_engine,https://github.com/elastic/integrations/tree/main/packages/security_detection_engine
sentinel_one,sentinel_one,https://github.com/elastic/integrations/tree/main/packages/sentinel_one
sentinel_one_cloud_funnel,sentinel_one_cloud_funnel,https://github.com/elastic/integrations/tree/main/packages/sentinel_one_cloud_funnel
servicenow,servicenow,https://github.com/elastic/integrations/tree/main/packages/servicenow
slack,slack,https://github.com/elastic/integrations/tree/main/packages/slack
snort,snort,https://github.com/elastic/integrations/tree/main/packages/snort
snyk,snyk,https://github.com/elastic/integrations/tree/main/packages/snyk
sonicwall_firewall,sonicwall_firewall,https://github.com/elastic/integrations/tree/main/packages/sonicwall_firewall
sophos,sophos,https://github.com/elastic/integrations/tree/main/packages/sophos
sophos_central,sophos_central,https://github.com/elastic/integrations/tree/main/packages/sophos_central
splunk,splunk,https://github.com/elastic/integrations/tree/main/packages/splunk
spring_boot,spring_boot,https://github.com/elastic/integrations/tree/main/packages/spring_boot
spycloud,spycloud,https://github.com/elastic/integrations/tree/main/packages/spycloud
sql_input,sql_input,https://github.com/elastic/integrations/tree/main/packages/sql_input
squid,squid,https://github.com/elastic/integrations/tree/main/packages/squid
stan,stan,https://github.com/elastic/integrations/tree/main/packages/stan
statsd_input,statsd_input,https://github.com/elastic/integrations/tree/main/packages/statsd_input
stormshield,stormshield,https://github.com/elastic/integrations/tree/main/packages/stormshield
sublime_security,sublime_security,https://github.com/elastic/integrations/tree/main/packages/sublime_security
suricata,suricata,https://github.com/elastic/integrations/tree/main/packages/suricata
swimlane,swimlane,https://github.com/elastic/integrations/tree/main/packages/swimlane
symantec_endpoint,symantec_endpoint,https://github.com/elastic/integrations/tree/main/packages/symantec_endpoint
symantec_endpoint_security,symantec_endpoint_security,https://github.com/elastic/integrations/tree/main/packages/symantec_endpoint_security
synthetics,synthetics,https://github.com/elastic/integrations/tree/main/packages/synthetics
synthetics_dashboards,synthetics_dashboards,https://github.com/elastic/integrations/tree/main/packages/synthetics_dashboards
sysdig,sysdig,https://github.com/elastic/integrations/tree/main/packages/sysdig
syslog_router,syslog_router,https://github.com/elastic/integrations/tree/main/packages/syslog_router
sysmon_linux,sysmon_linux,https://github.com/elastic/integrations/tree/main/packages/sysmon_linux
system,system,https://github.com/elastic/integrations/tree/main/packages/system
system_audit,system_audit,https://github.com/elastic/integrations/tree/main/packages/system_audit
tanium,tanium,https://github.com/elastic/integrations/tree/main/packages/tanium
tcp,tcp,https://github.com/elastic/integrations/tree/main/packages/tcp
teleport,teleport,https://github.com/elastic/integrations/tree/main/packages/teleport
tenable_io,tenable_io,https://github.com/elastic/integrations/tree/main/packages/tenable_io
tenable_ot_security,tenable_ot_security,https://github.com/elastic/integrations/tree/main/packages/tenable_ot_security
tenable_sc,tenable_sc,https://github.com/elastic/integrations/tree/main/packages/tenable_sc
tencent_cloud,tencent_cloud,https://github.com/elastic/integrations/tree/main/packages/tencent_cloud
tetragon,tetragon,https://github.com/elastic/integrations/tree/main/packages/tetragon
threat_map,threat_map,https://github.com/elastic/integrations/tree/main/packages/threat_map
thycotic_ss,thycotic_ss,https://github.com/elastic/integrations/tree/main/packages/thycotic_ss
tines,tines,https://github.com/elastic/integrations/tree/main/packages/tines
ti_abusech,ti_abusech,https://github.com/elastic/integrations/tree/main/packages/ti_abusech
ti_anomali,ti_anomali,https://github.com/elastic/integrations/tree/main/packages/ti_anomali
ti_cif3,ti_cif3,https://github.com/elastic/integrations/tree/main/packages/ti_cif3
ti_crowdstrike,ti_crowdstrike,https://github.com/elastic/integrations/tree/main/packages/ti_crowdstrike
ti_custom,ti_custom,https://github.com/elastic/integrations/tree/main/packages/ti_custom
ti_cybersixgill,ti_cybersixgill,https://github.com/elastic/integrations/tree/main/packages/ti_cybersixgill
ti_domaintools,ti_domaintools,https://github.com/elastic/integrations/tree/main/packages/ti_domaintools
ti_eclecticiq,ti_eclecticiq,https://github.com/elastic/integrations/tree/main/packages/ti_eclecticiq
ti_eset,ti_eset,https://github.com/elastic/integrations/tree/main/packages/ti_eset
ti_maltiverse,ti_maltiverse,https://github.com/elastic/integrations/tree/main/packages/ti_maltiverse
ti_mandiant_advantage,ti_mandiant_advantage,https://github.com/elastic/integrations/tree/main/packages/ti_mandiant_advantage
ti_misp,ti_misp,https://github.com/elastic/integrations/tree/main/packages/ti_misp
ti_opencti,ti_opencti,https://github.com/elastic/integrations/tree/main/packages/ti_opencti
ti_otx,ti_otx,https://github.com/elastic/integrations/tree/main/packages/ti_otx
ti_rapid7_threat_command,ti_rapid7_threat_command,https://github.com/elastic/integrations/tree/main/packages/ti_rapid7_threat_command
ti_recordedfuture,ti_recordedfuture,https://github.com/elastic/integrations/tree/main/packages/ti_recordedfuture
ti_threatconnect,ti_threatconnect,https://github.com/elastic/integrations/tree/main/packages/ti_threatconnect
ti_threatq,ti_threatq,https://github.com/elastic/integrations/tree/main/packages/ti_threatq
ti_util,ti_util,https://github.com/elastic/integrations/tree/main/packages/ti_util
tomcat,tomcat,https://github.com/elastic/integrations/tree/main/packages/tomcat
traefik,traefik,https://github.com/elastic/integrations/tree/main/packages/traefik
trellix_edr_cloud,trellix_edr_cloud,https://github.com/elastic/integrations/tree/main/packages/trellix_edr_cloud
trellix_epo_cloud,trellix_epo_cloud,https://github.com/elastic/integrations/tree/main/packages/trellix_epo_cloud
trendmicro,trendmicro,https://github.com/elastic/integrations/tree/main/packages/trendmicro
trend_micro_vision_one,trend_micro_vision_one,https://github.com/elastic/integrations/tree/main/packages/trend_micro_vision_one
tychon,tychon,https://github.com/elastic/integrations/tree/main/packages/tychon
udp,udp,https://github.com/elastic/integrations/tree/main/packages/udp
unifiedlogs,unifiedlogs,https://github.com/elastic/integrations/tree/main/packages/unifiedlogs
universal_profiling_agent,universal_profiling_agent,https://github.com/elastic/integrations/tree/main/packages/universal_profiling_agent
universal_profiling_collector,universal_profiling_collector,https://github.com/elastic/integrations/tree/main/packages/universal_profiling_collector
universal_profiling_symbolizer,universal_profiling_symbolizer,https://github.com/elastic/integrations/tree/main/packages/universal_profiling_symbolizer
varonis,varonis,https://github.com/elastic/integrations/tree/main/packages/varonis
vectra_detect,vectra_detect,https://github.com/elastic/integrations/tree/main/packages/vectra_detect
vectra_rux,vectra_rux,https://github.com/elastic/integrations/tree/main/packages/vectra_rux
vsphere,vsphere,https://github.com/elastic/integrations/tree/main/packages/vsphere
watchguard_firebox,watchguard_firebox,https://github.com/elastic/integrations/tree/main/packages/watchguard_firebox
websocket,websocket,https://github.com/elastic/integrations/tree/main/packages/websocket
websphere_application_server,websphere_application_server,https://github.com/elastic/integrations/tree/main/packages/websphere_application_server
windows,windows,https://github.com/elastic/integrations/tree/main/packages/windows
windows_etw,windows_etw,https://github.com/elastic/integrations/tree/main/packages/windows_etw
winlog,winlog,https://github.com/elastic/integrations/tree/main/packages/winlog
wiz,wiz,https://github.com/elastic/integrations/tree/main/packages/wiz
zeek,zeek,https://github.com/elastic/integrations/tree/main/packages/zeek
zerofox,zerofox,https://github.com/elastic/integrations/tree/main/packages/zerofox
zeronetworks,zeronetworks,https://github.com/elastic/integrations/tree/main/packages/zeronetworks
zookeeper,zookeeper,https://github.com/elastic/integrations/tree/main/packages/zookeeper
zoom,zoom,https://github.com/elastic/integrations/tree/main/packages/zoom
zscaler_zia,zscaler_zia,https://github.com/elastic/integrations/tree/main/packages/zscaler_zia
zscaler_zpa,zscaler_zpa,https://github.com/elastic/integrations/tree/main/packages/zscaler_zpa
ENDMSG
```
---
### rag/extract_logtypes.py
```bash
cat > "/opt/SmartSOC/web/rag/extract_logtypes.py" <<"ENDMSG"
import os
import csv
import re

def extract_elastic_logtypes():
    # Return a list of sub-directories in the Elastic packages directory
    packages_dir = "./rag/repos/elastic_repo/packages"
    try:
        logtypes = [d for d in os.listdir(packages_dir) if os.path.isdir(os.path.join(packages_dir, d))]
        
        # Write logtypes to CSV file
        csv_filename = "./rag/elastic_logtypes.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Package', 'Logtype', 'Documentation_URL'])
            
            # Write data rows
            for logtype in logtypes:
                documentation_url = f"https://github.com/elastic/integrations/tree/main/packages/{logtype}"
                writer.writerow([logtype, logtype, documentation_url])
        
        print(f"Successfully wrote {len(logtypes)} logtypes to '{csv_filename}'")
        return logtypes
        
    except FileNotFoundError:
        print(f"Directory '{packages_dir}' not found.")
        return []


def extract_splunk_sourcetypes():
    """Extract sourcetypes from all Splunk packages and write to CSV."""
    packages_dir = "./rag/repos/splunk_repo"
    csv_filename = "./rag/splunk_sourcetypes.csv"
    
    try:
        # Get all subdirectories in splunk_repo
        package_names = [d for d in os.listdir(packages_dir) 
                        if os.path.isdir(os.path.join(packages_dir, d))]
        
        # Open CSV file for writing
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Package', 'Sourcetype', 'Documentation_URL'])
            
            total_sourcetypes = 0
            
            # Process each package
            for package_name in package_names:
                package_path = os.path.join(packages_dir, package_name)
                
                # Extract documentation URL once per package from README.txt
                
                readme_path = os.path.join(package_path, "README.txt")
                try:
                    with open(readme_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        # Look for URLs (http:// or https://)
                        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                        match = re.search(url_pattern, content)
                        if match:
                            documentation_url =  match.group(0)
                        else:
                            documentation_url = ""
                except FileNotFoundError:
                    pass

                # Extract sourcetypes from props.conf for this package
                sourcetypes = []
                props_conf_path = os.path.join(package_path, "default", "props.conf")
                
                try:
                    with open(props_conf_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()

                    # Find all stanza headers [sourcetype_name]
                    # Match square brackets with content inside, excluding comments
                    pattern = r'^\s*\[([^\]]+)\]\s*$'
                    matches = re.findall(pattern, content, re.MULTILINE)

                    for match in matches:
                        # Clean up the sourcetype name
                        sourcetype = match.strip()
                        # Skip if it contains wildcards or special characters that indicate it's not a sourcetype
                        if not any(char in sourcetype for char in ['*', '?', '...', 'default']):
                            sourcetypes.append(sourcetype)
                
                except FileNotFoundError:
                    print(f"File '{props_conf_path}' not found for package '{package_name}'.")
                
                # Write rows for each sourcetype
                for sourcetype in sourcetypes:
                    writer.writerow([package_name, sourcetype, documentation_url])
                    total_sourcetypes += 1
                
                if sourcetypes:
                    print(f"Package '{package_name}': Found {len(sourcetypes)} sourcetypes")
                else:
                    print(f"Package '{package_name}': No sourcetypes found")

        print(f"Successfully wrote {total_sourcetypes} sourcetypes from {len(package_names)} packages to {csv_filename}")

    except FileNotFoundError:
        print(f"Directory '{packages_dir}' not found.")
        return []

# extract_elastic_logtypes()

# extract_splunk_sourcetypes()

ENDMSG
```
---
### rag/splunk_fields.csv
```bash
cat > "/opt/SmartSOC/web/rag/splunk_fields.csv" <<"ENDMSG"
Dataset_name,Field_name,Data_type,Description,Notes
Alerts,app,string,"The system, service, or application that generated the alert event. Examples include, but are not limited to the following: GuardDuty, SecurityCenter, 3rd party services, win:app:trendmicro, vmware, nagios.","recommended
required for pytest-splunk-addon"
Alerts,body,string,The body of a message. This field is deprecated in favor of description.,required for pytest-splunk-addon
Alerts,description,string,The description of the alert event.,
Alerts,dest,string,"The object that is the target of the alert event. Examples include an email address, SNMP trap, or virtual machine id. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
Alerts,dest_bunit,string,The business unit associated with the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,dest_category,string,The category of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,dest_priority,string,The priority of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,dest_type,string,"The type of the destination object, such as instance, storage, firewall.",
Alerts,id,string,The unique identifier of the alert event.,required for pytest-splunk-addon
Alerts,mitre_technique_id,string,"The MITRE ATT&CK technique ID of the alert event, searchable at https://attack.mitre.org/techniques.",
Alerts,severity,string,"The severity of the alert event.Note: This field is a string. Specific values are required. Use the severity_id field for severity ID fields that are integer data types. Specific values are required. Use vendor_severity for the vendor's own human-readable strings (such as Good, Bad, Really Bad, and so on).","recommended
required for pytest-splunk-addon
prescribed values:critical, high, medium, low, informational, unknown"
Alerts,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
Alerts,signature_id,string,"The unique ID that identifies the vendor specific policy or rule that generated the alert event.
For example:

Policy:IAMUser/RootCredentialUsage.
0x00011f00",recommended
Alerts,src,string,"The object that is the actor of the alert event. You can alias this from more specific fields, such as src_host, src_ip, or src_name.",recommended
Alerts,src_bunit,string,The business unit associated with the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,src_category,string,The category of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,src_priority,string,The priority of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,src_type,string,"The type of the source object, such as instance, storage, firewall.",
Alerts,subject,string,The message subject. This field is deprecated in favor of signature.,
Alerts,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
Alerts,type,string,The alert event type.,"recommended
required for pytest-splunk-addon
prescribed values:alarm, alert, event, task, warning, unknown"
Alerts,user,string,The user involved in the alert event.,recommended
Alerts,user_bunit,string,The business unit of the user involved in the alert event. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,user_category,string,The category of the user involved in the alert event. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,user_name,string,The name of the user involved in the alert event.,recommended
Alerts,user_priority,string,The priority of the user involved in the alert event. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Alerts,vendor_account,string,"The account associated with the alert event. The account represents the organization, or a Cloud  customer or a Cloud account.",
Alerts,vendor_region,string,"The data center region involved in the alert event, such as us-west-2.",
All_Application_State,dest,string,"The compute resource where the service is installed. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.",recommended
All_Application_State,dest_bunit,string,,These fields are automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for these fields when writing add-ons.
All_Application_State,dest_category,string,,
All_Application_State,dest_priority,string,,
All_Application_State,dest_requires_av,boolean,,
All_Application_State,dest_should_timesync,boolean,,
All_Application_State,dest_should_update,boolean,,
All_Application_State,process,string,"The name of a process or service file, such as sqlsrvr.exe or httpd.Note: This field is not appropriate for service or daemon names, such as SQL Server or Apache Web Server. Service or daemon names belong to the service field (see below).",recommended
All_Application_State,process_name,string,The name of a process.,
All_Application_State,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Application_State,user,string,"The user account the service is running as, such as System or httpdsvc.",
Ports,dest_port,number,"Network ports communicated to by the process, such as 53.",recommended
Ports,transport,string,"The network ports listened to by the application process, such as tcp, udp, etc.",recommended
Ports,transport_dest_port,string,"Calculated as transport/dest_port, such as tcp/53.",
Processes,cpu_load_mhz,number,CPU Load in megahertz,
Processes,cpu_load_percent,number,CPU Load in percent,
Processes,cpu_time,string,CPU Time,
Processes,mem_used,number,Memory used in bytes,
Services,service,string,"The name of the service, such as SQL Server or Apache Web Server.Note: This field is not appropriate for filenames, such as sqlsrvr.exe or httpd. Filenames should belong to the process field instead. Also, note that field is a string. Use the service_id field for service ID fields that are integer data types.",recommended
Services,service_id,string,A numeric indicator for a service.,recommended
Services,start_mode,string,The start mode for the service.,"disabled, manual, auto.recommended"
Services,status,string,The status of the service.,"critical, started, stopped, warningrecommended"
Authentication,action,string,The action performed on the resource.,"Prescribed values: success, failure, pending, errorRecommended. Also, required for pytest-splunk-addon"
Authentication,app,string,The application involved in the event.,"ssh splunk win:localsignin.amazonaws.comRecommended. Also, required for pytest-splunk-addon"
Authentication,authentication_method,string,The method used to authenticate the request.,Optional
Authentication,authentication_service,string,The service used to authenticate the request.,"Okta, ActiveDirectory, AzureADOptional"
Authentication,dest,string,The target host involved in the authentication. You can alias this from more specific fields.,"dest_host, dest_ip,  dest_nt_hostRecommended"
Authentication,dest_bunit,string,The business unit of the authentication target.,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,dest_category,string,The category of the authentication target.,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.email_server or SOX-compliant
Authentication,dest_nt_domain,string,"The name of the Active Directory used by the authentication target, if applicable.",
Authentication,dest_priority,string,The priority of the authentication target.,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,duration,number,"The amount of time for the completion of the authentication event, in seconds.",
Authentication,process,number,"The full path and the name of the executable for the process that attempted the log in. For example, it is a ""Process Name"" in Windows such as C:\Windows\System32\svchost.exe.",Optional
Authentication,reason_id,string,"The reason for login failure. For example ""0xC0000234"".",Optional
Authentication,response_time,number,"The amount of time it took to receive a response in the authentication event, in seconds.",
Authentication,signature,string,A human-readable signature name.,
Authentication,signature_id,string,The unique identifier or event code of the event signature.,
Authentication,src,string,The source involved in the authentication. In the case of endpoint protection authentication the src is the client.,"You can alias this from more specific fields.src_host, src_ip, or src_nt_host.Do not confuse src with the event source or sourcetype fields.Recommended"
Authentication,src_bunit,string,The business unit of the authentication source.,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,src_category,string,The category of the authentication source.,email_server or SOX-compliant
Authentication,src_nt_domain,string,"The name of the Active Directory used by the authentication source, if applicable.",
Authentication,src_priority,string,The priority of the authentication source.,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,src_user,string,"In privilege escalation events, src_user represents the user who initiated the privilege escalation.",This field is unnecessary when an escalation has not been performed.Recommended
Authentication,src_user_bunit,string,The business unit of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,src_user_category,string,The category of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,src_user_id,string,The unique id of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed.
Authentication,src_user_priority,string,The priority of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,src_user_role,string,The role of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed.
Authentication,src_user_type,string,The type of the user who initiated the privilege escalation.,This field is unnecessary when an escalation has not been performed.
Authentication,tag,string,This automatically-generated field is used to access tags from within data models.,Do not define extractions for this field when writing add-ons.
Authentication,user,string,The actual string or identifier that a user is logging in with.,"This is the user involved in the event, or who initiated the event. For authentication privilege escalation events, this should represent the user string or identifier targeted by the escalation. Recommended. Also, required for pytest-splunk-addon"
Authentication,user_agent,string,The user agent through which the request was made.Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) or aws-cli/2.0.0 Python/3.7.4 Darwin/18.7.0 botocore/2.0.0dev4,
Authentication,user_bunit,string,"The business unit of the user involved in the event, or who initiated the event.",For authentication privilege escalation events this should represent the user targeted by the escalation. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.
Authentication,user_category,string,"The category of the user involved in the event, or who initiated the event.","For authentication privilege escalation events, this should represent the user targeted by the escalation. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons."
Authentication,user_id,string,The unique id of the user involved in the event.,"For authentication privilege escalation events, this should represent the user targeted by the escalation."
Authentication,user_priority,string,"The priority of the user involved in the event, or who initiated the event.","For authentication privilege escalation events, this should represent the user targeted by the escalation. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons."
Authentication,user_role,string,"The role of the user involved in the event, or who initiated the event.","For authentication privilege escalation events, this should represent the user role targeted by the escalation."
Authentication,user_type,string,"The type of the user involved in the event or who initiated the event.IAMUser, Admin, or System.","For authentication privilege escalation events, this should represent the user type targeted by the escalation."
All_Certificates,dest,string,The target in the certificate management event.,
All_Certificates,dest_bunit,string,The business unit of the target.This field is automatically provided by Asset and Identity correlation features of applications like Splunk Enterprise Security.,
All_Certificates,dest_category,string,The category of the target.This field is automatically provided by Asset and Identity correlation features of applications like the Splunk Enterprise Security.,"other:email_server, SOX-compliant"
All_Certificates,dest_port,number,The port number of the target.,
All_Certificates,dest_priority,string,The priority of the target. Field is automatically provided by the Asset and Identity correlation features of applications such as Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Certificates,duration,number,"The amount of time for the completion of the certificate management event, in seconds.",
All_Certificates,response_time,number,"The amount of time it took to receive a response in the certificate management event, if applicable.",
All_Certificates,src,string,"The source involved in the certificate management event. You can alias this from more specific fields, such as src_host, src_ip, or src_nt_host.Note: Do not confuse src with the event source or sourcetype fields.",
All_Certificates,src_bunit,string,The business unit of the certificate management source.This field is automatically provided by Asset and Identity correlation features of applications like Splunk Enterprise Security.,
All_Certificates,src_category,string,The category of the certificate management source.This field is automatically provided by Asset and Identity correlation features of applications like the Splunk Enterprise Security.,"other:email_server, SOX-compliant"
All_Certificates,src_port,number,The port number of the source.,
All_Certificates,src_priority,string,The priority of the certificate management source.,
All_Certificates,tag,string,This automatically generated field is used to access tags from within datamodels. Add-on builders do not need to populate it.,
All_Certificates,transport,string,The transport protocol of the Network Traffic involved with this certificate.,
SSL,ssl_end_time,time,The expiry time of the certificate. Needs to be converted to UNIX time for calculations in dashboards.,recommended
SSL,ssl_engine,string,The name of the signature engine that created the certificate.,
SSL,ssl_hash,string,The hash of the certificate.,recommended
SSL,ssl_is_valid,boolean,Indicator of whether the ssl certificate is valid or not.,"prescribed values:true, false, 1, 0"
SSL,ssl_issuer,string,The certificate issuer's RFC2253 Distinguished Name.,"recommended
required for pytest-splunk-addon"
SSL,ssl_issuer_common_name,string,The certificate issuer's common name.,"recommended
required for pytest-splunk-addon"
SSL,ssl_issuer_email,string,The certificate issuer's email address.,
SSL,ssl_issuer_email_domain,string,The domain name contained within the certificate issuer's email address.,recommended
SSL,ssl_issuer_locality,string,The certificate issuer's locality.,
SSL,ssl_issuer_organization,string,The certificate issuer's organization.,
SSL,ssl_issuer_state,string,The certificate issuer's state of residence.,
SSL,ssl_issuer_street,string,The certificate issuer's street address.,
SSL,ssl_issuer_unit,string,The certificate issuer's organizational unit.,
SSL,ssl_name,string,The name of the ssl certificate.,
SSL,ssl_policies,string,The Object Identification Numbers's of the certificate's policies in a comma separated string.,
SSL,ssl_publickey,string,The certificate's public key.,
SSL,ssl_publickey_algorithm,string,The algorithm used to create the public key.,
SSL,ssl_serial,string,The certificate's serial number.,"recommended
required for pytest-splunk-addon"
SSL,ssl_session_id,string,The session identifier for this certificate.,
SSL,ssl_signature_algorithm,string,The algorithm used by the Certificate Authority to sign the certificate.,
SSL,ssl_start_time,time,This is the start date and time for this certificate's validity. Needs to be converted to UNIX time for calculations in dashboards.,recommended
SSL,ssl_subject,string,The certificate owner's RFC2253 Distinguished Name.,"recommended
required for pytest-splunk-addon"
SSL,ssl_subject_common_name,string,This certificate owner's common name.,"recommended
required for pytest-splunk-addon"
SSL,ssl_subject_email,string,The certificate owner's e-mail address.,
SSL,ssl_subject_email_domain,string,The domain name contained within the certificate subject's email address.,recommended
SSL,ssl_subject_locality,string,The certificate owner's locality.,
SSL,ssl_subject_organization,string,The certificate owner's organization.,required for pytest-splunk-addon
SSL,ssl_subject_state,string,The certificate owner's state of residence.,
SSL,ssl_subject_street,string,The certificate owner's street address.,
SSL,ssl_subject_unit,string,The certificate owner's organizational unit.,
SSL,ssl_validity_window,number,The length of time (in seconds) for which this certificate is valid.,required for pytest-splunk-addon
SSL,ssl_version,string,The ssl version of this certificate.,
All_Changes,action,string,"The action attempted on the resource, regardless of success or failure.","recommended
required for pytest-splunk-addon
prescribed values:acl_modified,cleared,created, deleted, modified, stopped,lockout, read, logoff, updated,  started, restarted,unlocked"
All_Changes,change_type,string,"The type of change, such as filesystem or AAA (authentication, authorization, and accounting).","recommended
required for pytest-splunk-addon
prescribed values: NA"
All_Changes,command,string,The command that initiated the change.,"recommended
required for pytest-splunk-addon"
All_Changes,dest,string,"The resource where change occurred. You can alias this from more specific fields not included in this data model, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
All_Changes,dvc,string,"The device that reported the change, if applicable, such as a FIP or CIM server. You can alias this from more specific fields not included in this data model, such as dvc_host, dvc_ip, or dvc_name.","recommended
required for pytest-splunk-addon"
All_Changes,image_id,string,"For create instance events, this field represents the image ID used for creating the instance such as the OS, applications, installed libraries, and so on.","recommended
required for pytest-splunk-addon"
All_Changes,object,string,"Name of the affected object on the resource (such as a router interface, user account, or server volume).","recommended
required for pytest-splunk-addon"
All_Changes,object_attrs,string,"The object's attributes and their values. The attributes and values can be those that are updated on a resource object, or those that are not updated but are essential attributes.","recommended
required for pytest-splunk-addon"
All_Changes,object_category,string,"Generic name for the class of the updated resource object. Expected values may be specific to an app, for example: registry, directory, file, group, user, bucket, instance.","recommended
required for pytest-splunk-addon"
All_Changes,object_id,string,"The unique updated resource object ID as presented to the system, if applicable (for instance, a SID, UUID, or GUID value).","recommended
required for pytest-splunk-addon"
All_Changes,object_path,string,"The path of the modified resource object, if applicable (such as a file, directory, or volume).","recommended
required for pytest-splunk-addon"
All_Changes,result,string,"The vendor-specific result of a change, or clarification of an action status. For instance, status=failure may be accompanied by result=blocked by policy or result=disk full.",recommended
All_Changes,result_id,string,A result indicator for an action status.,recommended
All_Changes,src,string,"The resource where the change was originated. You can alias this from more specific fields not included in the data model, such as src_host, src_ip, or src_name.",recommended
All_Changes,status,string,Status of the update.,"recommended
required for pytest-splunk-addon
prescribed values:success, failure"
All_Changes,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
All_Changes,user,string,"The user or entity performing the change. For account changes, this is the account that was changed. See src_user for user or entity performing the change.","recommended
required for pytest-splunk-addon"
All_Changes,user_agent,string,"The user agent through which the request was made, such as Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) or aws-cli/2.0.0 Python/3.7.4 Darwin/18.7.0 botocore/2.0.0dev4.",
All_Changes,user_name,string,"The user name of the user or entity performing the change. For account changes, this is the account that was changed (see src_user_name).",recommended
All_Changes,user_type,string,"The type of the user involved in the event or who initiated the event, such as IAMUser, Admin, or System. For account management events, this should represent the type of the user changed by the request.",
All_Changes,vendor_account,string,"The account that manages the user that initiated the request. The account represents the organization, or a Cloud  customer or a Cloud account.",
All_Changes,vendor_product,string,The vendor and product or service that detected the change. This field can be automatically populated by vendor and product fields in your data.,"recommended
required for pytest-splunk-addon"
All_Changes,vendor_region,string,"The data center region where the change occurred, such as us-west-2.",
Account_Management,dest_nt_domain,string,"The NT domain of the destination, if applicable.",recommended
Account_Management,src_nt_domain,string,"The NT domain of the source, if applicable.",recommended
Account_Management,src_user,string,"For account changes, the user or entity performing the change.",recommended
Account_Management,src_user_name,string,"For account changes, the user name of the user or entity performing the change.",recommended
Account_Management,src_user_type,string,"For account management events, this should represent the type of the user changed by the request.",
Network_Changes,dest_ip_range,string,"For network events, the outgoing traffic for a specific destination IP address range. Specify a single IP address or an IP address range in CIDR notation. For example, 203.0.113.5 or 203.0.113.5/32.",
Network_Changes,dest_port_range,string,"For network events, this field represents destination port or range. For example, 80 or 8000 - 8080 or 80,443.",
Network_Changes,direction,string,"For network events, this field represents whether the traffic is inbound or outbound.",
Network_Changes,rule_action,string,"For network events, this field represents whether to allow or deny traffic.",
Network_Changes,src_ip_range,string,"For network events, this field represents the incoming traffic from a specific source IP address or range. Specify a single IP address or an IP address range in CIDR notation. For example, 203.0.113.5 or 203.0.113.5/32.",
Network_Changes,src_port_range,string,"For network events, this field represents source port or range. For example, 80 or 8000 - 8080 or 80,443.",
All_Changes,action,string,The action performed on the resource.,"Values:acl_modified, cleared, created, deleted, modified, read, stopped, updatedrecommended"
All_Changes,change_type,string,"The type of change, such as filesystem or AAA (authentication, authorization, and accounting).",Values: restartrecommended
All_Changes,command,string,The command that initiated the change.,recommended
All_Changes,dest,string,"The resource where change occurred. You can alias this from more specific fields not included in this data model, such as dest_host, dest_ip, or dest_name.",recommended
All_Changes,dvc,string,"The device that reported the change, if applicable, such as a FIP or CIM server. You can alias this from more specific fields not included in this data model, such as dvc_host, dvc_ip, or dvc_name.",recommended
All_Changes,object,string,"Name of the affected object on the resource (such as a router interface, user account, or server volume).",recommended
All_Changes,object_attrs,string,"The attributes that were updated on the updated resource object, if applicable.",recommended
All_Changes,object_category,string,Generic name for the class of the updated resource object. Expected values may be specific to an app.,"Values:directory, file, group, registry, userrecommended"
All_Changes,object_id,string,"The unique updated resource object ID as presented to the system, if applicable (for instance, a SID, UUID, or GUID value).",recommended
All_Changes,object_path,string,"The path of the modified resource object, if applicable (such as a file, directory, or volume).",recommended
All_Changes,result,string,"The vendor-specific result of a change, or clarification of an action status. For instance, status=failure may be accompanied by result=blocked by policy or result=disk full. result is a string. Please use a msg_severity_id field (not included in the data model) for severity ID fields that are integer data types.",Values: lockoutrecommended
All_Changes,result_id,string,A result indicator for an action status.,recommended
All_Changes,src,string,"The resource where the change was originated. You can alias this from more specific fields not included in the data model, such as src_host, src_ip, or src_name.",recommended
All_Changes,status,string,Status of the update.,"Values:success, failurerecommended"
All_Changes,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
All_Changes,user,string,"The user or entity performing the change. For account changes, this is the account that was changed. See src_user for user or entity performing the change.",recommended
All_Changes,vendor_product,string,The vendor and product or service that detected the change. This field can be automatically populated by vendor and product fields in your data.,recommended
Account_Management,dest_nt_domain,string,"The NT domain of the destination, if applicable.",
Account_Management,src_nt_domain,string,"The NT domain of the source, if applicable.",
Account_Management,src_user,string,"For account changes, the user or entity performing the change.",
Filesystem_Changes,file_access_time,time,The time the file (the object of the event) was accessed.,
Filesystem_Changes,file_acl,string,Access controls associated with the file affected by the event.,
Filesystem_Changes,file_create_time,time,The time the file (the object of the event) was created.,
Filesystem_Changes,file_hash,string,A cryptographic identifier assigned to the file object affected by the event.,
Filesystem_Changes,file_modify_time,time,The time the file (the object of the event) was altered.,
Filesystem_Changes,file_name,string,The name of the file that is the object of the event (without location information related to local file or directory structure).,
Filesystem_Changes,file_path,string,"The location of the file that is the object of the event, in local file and directory structure terms.",
Filesystem_Changes,file_size,number,"The size of the file that is the object of the event, in kilobytes.",
All_Inventory,description,string,The description of the inventory system.,
All_Inventory,dest,string,"The system where the data originated, the source of the event. You can alias' this from more specific fields, such as dest_host, dest_ip, or dest_name.",
All_Inventory,dest_bunit,string,The business unit of the system where the data is going. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Inventory,dest_category,string,"The category of the system where the data is going, such as email_server or SOX-compliant. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Inventory,dest_priority,string,The priority of the system where the data is going. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Inventory,enabled,boolean,Indicates whether the resource is enabled or disabled.,
All_Inventory,family,string,"The product family of the resource, such as 686_64 or RISC.",
All_Inventory,hypervisor_id,string,"The hypervisor identifier, if applicable.",
All_Inventory,serial,string,The serial number of the resource.,
All_Inventory,status,string,The current reported state of the resource.,
All_Inventory,tag,string,Splunk uses this automatically generated field to access tags from within data models. You do not need to populate it.,
All_Inventory,vendor_product,string,"The vendor and product name of the resource, such as Cisco Catalyst 3850. This field can be automatically populated by vendor and product fields in your data.",
All_Inventory,version,string,"The  version of a computer resource, such as 2008r2 or 3.0.0.",
CPU,cpu_cores,number,"The number of CPU cores reported by the resource (total, not per CPU).",
CPU,cpu_count,number,The number of CPUs reported by the resource.,
CPU,cpu_mhz,number,The maximum speed of the CPU reported by the resource (in megahertz).,
Memory,mem,number,"The total amount of memory installed in or allocated to the resource, in megabytes.",
Network,dest_ip,string,The IP address for the system that the data is going to.,
Network,dns,string,The domain name server for the resource.,
Network,inline_nat,string,Identifies whether the resource is a network address translation pool.,
Network,interface,string,"The network interfaces of the computing resource, such as eth0, eth1 or Wired Ethernet Connection, Teredo Tunneling Pseudo-Interface.",
Network,ip,string,"The network address of the computing resource, such as 192.168.1.1 or E80:0000:0000:0000:0202:B3FF:FE1E:8329.",
Network,lb_method,string,"The load balancing method used by the computing resource such as method, round robin, or least weight.",
Network,mac,string,"A MAC (media access control) address associated with the resource, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.",
Network,name,string,A name field provided in some data sources.,
Network,node,string,Represents a node hit.,
Network,node_port,number,The number of the destination port on the server that you requested from.,
Network,src_ip,string,The IP address for the system from which the data originates.,
Network,vip_port,number,The port number for the virtual IP address (VIP). A VIP allows multiple MACs to use one IP address. VIPs are often used by load balancers.,
OS,os,string,"The operating system of the resource, such as Microsoft Windows Server 2008r2. This field is constructed from vendor_product and version fields.",
Storage,array,string,"The array that the storage resource is a member of, if applicable",
Storage,blocksize,number,"The block size used by the storage resource, in kilobytes.",
Storage,cluster,string,"The index cluster that the resource is a member of, if applicable.",
Storage,fd_max,number,The maximum number of file descriptors available.,
Storage,latency,number,"The latency reported by the resource, in milliseconds.",
Storage,mount,string,The path at which a storage resource is mounted.,
Storage,parent,string,"A higher level object that this resource is owned by, if applicable.",
Storage,read_blocks,number,The maximum possible number of blocks read per second during a polling period .,
Storage,read_latency,number,"For a polling period, the average amount of time elapsed until a read request is filled by the host disks (in ms).",
Storage,read_ops,number,The total number of read operations in the polling period.,
Storage,storage,number,"The amount of storage capacity allocated to the resource, in megabytes.",
Storage,write_blocks,number,The maximum possible number of blocks written per second during a polling period.,
Storage,write_latency,number,"For a polling period, the average amount of time elapsed until a write request is filled by the host disks (in ms).",
Storage,write_ops,number,The total number of write operations in the polling period.,
User,interactive,boolean,Indicates whether a locally defined account on a resource can be interactively logged in.,
User,password,string,"Displays the stored password(s) for a locally defined account, if it has any. For instance, an add-on may report the password column from /etc/passwd in this field.",
User,shell,string,Indicates the shell program used by a locally defined account.,
User,user,string,The full name of a locally defined account.,
User,user_bunit,string,The business unit of the locally-defined user account. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
User,user_category,string,"The category of the system where the data originated, such as email_server or SOX-compliant. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
User,user_id,number,The user identification for a locally defined account.,
User,user_priority,string,The priority of a locally-defined account. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Virtual_OS,hypervisor,string,The hypervisor parent of a virtual guest OS.,
Snapshot,size,number,"The snapshot file size, in megabytes.",
Snapshot,snapshot,string,The name of a snapshot file.,
Snapshot,time,time,The time at which the snapshot was taken.,
Data_Access,action,string,The data access action taken by the user.,"recommended
prescribed values:commented, copied, created, deleted, disabled, downloaded, enabled, granted, forwarded, modified, read, revoked, shared, stopped, uncommented, unlocked, unshared, updated, uploaded,"
Data_Access,app,string,The application involved in the event.,recommended
Data_Access,app_id,string,Application ID as defined by the vendor.,
Data_Access,dest,string,"The destination where the data resides or where it is being accessed, such as the product or application. You can alias this from more specific fields not included in this data model, such as dest_host, dest_ip, dest_url, or dest_name.",recommended
Data_Access,dest_name,string,Name of the destination as defined by the vendor.,
Data_Access,dest_url,string,"Url of the product, application, or object.",
Data_Access,dvc,string,The device that reported the data access event.,
Data_Access,email,string,"The email address of the user involved in the event, or who initiated the event.",
Data_Access,object,string,Resource object name on which the action was performed by a user.,recommended
Data_Access,object_attrs,string,"The object's attributes and their values. The attributes and values can be those that are updated on a resource object, or those that are not updated but are essential attributes.",recommended
Data_Access,object_category,string,"Generic name for the class of the updated resource object. Expected values may be specific to an app. For example, collaboration, file, folder, comment, task, note, and so on.",recommended
Data_Access,object_id,string,"The unique updated resource object ID as presented to the system, if applicable. For example, a source_folder_id, doc_id.",recommended
Data_Access,object_path,string,"The path of the modified resource object, if applicable, such as a file, directory, or volume.",
Data_Access,object_size,string,The size of the modified resource object.,recommended
Data_Access,owner,string,Resource owner.,
Data_Access,owner_email,string,Email of the resource owner.,
Data_Access,owner_id,string,ID of the owner as defined by the vendor.,
Data_Access,parent_object,string,Parent of the object name on which the action was performed by a user.,
Data_Access,parent_object_id,string,Parent object ID,
Data_Access,parent_object_category,string,Object category of the parent object on which action was performed by a user.,
Data_Access,signature,string,A human-readable signature name.,
Data_Access,signature_id,string,The unique identifier or event code of the event signature.,optional
Data_Access,src,string,The endpoint client host.,recommended
Data_Access,vendor_account,string,"Account associated with the event. The account represents the organization, or a Cloud  customer or a Cloud account.",recommended
Data_Access,user,string,"The user involved in the event, or who initiated the event.",recommended
Data_Access,user_agent,string,"The user agent through which the request was made, such as Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) or aws-cli/2.0.0 Python/3.7.4 Darwin/18.7.0 botocore/2.0.0dev4",recommended
Data_Access,user_group,string,"The group of the user involved in the event, or who initiated the event.",
Data_Access,user_id,string,"The unique id of the user involved in the event. For authentication privilege escalation events, this should represent the user targeted by the escalation.",optional
Data_Access,user_name,string,"The user name of the user or entity performing the change. For account changes, this is the account that was changed (see src_user_name). Use this field for a friendlier name, for example, with AWS events if you do not have Assets and Identities configured in Enterprise Security and are not getting a friendly name from user.",recommended
Data_Access,user_email,string,The email address of the user or entity involved in the event.,optional
Data_Access,user_role,string,"The role of the user involved in the event, or who initiated the event.",
Data_Access,user_type,string,"The type of the user involved in the event or who initiated the event, such as IAMUser, Admin, or System. For account management events, this should represent the type of the user changed by the request.",optional
Data_Access,vendor_product,string,The vendor and product name of the vendor.,recommended
Data_Access,vendor_product_id,string,The vendor and product name ID as defined by the vendor.,
Data_Access,vendor_region,string,"The data center region where the change occurred, such as us-west-2.",optional
DLP_Incidents,action,string,The action taken by the DLP device.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,app,string,The application involved in the event.,required for pytest-splunk-addon
DLP_Incidents,category,string,The category of the DLP event.,"recommenderd
required for pytest-splunk-addon"
DLP_Incidents,dest,string,The target of the DLP event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,dest_bunit,string,The business unit of the DLP target. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dest_category,string,The category of the DLP target. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dest_priority,string,The priority of the DLP target. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dest_zone,string,The zone of the DLP target.,
DLP_Incidents,dlp_type,string,The type of DLP system that generated the event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,dvc,string,The device that reported the DLP event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,dvc_bunit,string,The business unit of the DLP target. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dvc_category,string,The category of the DLP device. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dvc_priority,string,The priority of the DLP device. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,dvc_zone,string,The zone of the DLP device.,
DLP_Incidents,object,string,The name of the affected object.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,object_category,string,The category of the affected object.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,object_path,string,The path of the affected object.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,severity,string,The severity of the DLP event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
DLP_Incidents,signature,string,The name of the DLP event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,signature_id,string,The unique identifier or event code of the event signature.,
DLP_Incidents,src,string,The source of the DLP event.,recommended
DLP_Incidents,src_bunit,string,The business unit of the DLP source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_category,string,The category of the DLP source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_priority,string,The priority of the DLP source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_user,string,The source user of the DLP event.,"recommended
required for pytest-splunk-addon"
DLP_Incidents,src_user_bunit,string,The business unit of the DLP source user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_user_category,string,The category of the DLP source user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_user_priority,string,The priority of the DLP source user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,src_zone,string,The zone of the DLP source.,
DLP_Incidents,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,user,string,The target user of the DLP event.,recommended
DLP_Incidents,user_bunit,string,The business unit of the DLP user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,user_category,string,The category of the DLP user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,user_priority,string,The priority of the DLP user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DLP_Incidents,vendor_product,string,The vendor and product name of the DLP system.,recommended
All_Databases,dest,string,"The destination of the database event. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.",
All_Databases,dest_bunit,string,The business unit of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,dest_category,string,The category of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,dest_priority,string,"The priority of the destination, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Databases,duration,number,"The amount of time for the completion of the database event, in seconds.",
All_Databases,object,string,The name of the database object.,
All_Databases,response_time,number,"The amount of time it took to receive a response in the database event, in seconds.",
All_Databases,src,string,"The source of the database event. You can alias this from more specific fields, such as src_host, src_ip, or src_name.",
All_Databases,src_bunit,string,The business unit of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,src_category,string,The category of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,src_priority,string,The priority of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Databases,user,string,Name of the database process user.,
All_Databases,user_bunit,string,The business unit of the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,user_category,string,The category associated with the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,user_priority,string,The priority of the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Databases,vendor_product,string,The vendor and product name of the database system. This field can be automatically populated by vendor and product fields in your data.,
Database_Instance,instance_name,string,The name of the database instance.,
Database_Instance,instance_version,string,The version of the database instance.,
Database_Instance,process_limit,number,The maximum number of processes that the database instance can handle.,
Database_Instance,session_limit,number,The maximum number of sessions that the database instance can handle.,
Instance_Stats,availability,string,The status of the database server.,"prescribed values:Available, Not Available"
Instance_Stats,avg_executions,number,The average number of executions for the database instance.,
Instance_Stats,dump_area_used,string,The amount of the database dump area that has been used.,
Instance_Stats,instance_reads,number,The total number of reads for the database instance.,
Instance_Stats,instance_writes,number,The total number of writes for the database instance.,
Instance_Stats,number_of_users,number,The total number of users for the database instance.,
Instance_Stats,processes,number,The number of processes currently running for the database instance.,
Instance_Stats,sessions,number,The total number of sessions currently in use for the database instance.,
Instance_Stats,sga_buffer_cache_size,number,"The total size of the buffer cache for the database instance, in bytes.",
Instance_Stats,sga_buffer_hit_limit,number,The maximum number of number of buffers that can be hit in the database instance without finding a free buffer.,
Instance_Stats,sga_data_dict_hit_ratio,number,The hit-to-miss ratio for the database instance's data dictionary.,
Instance_Stats,sga_fixed_area_size,number,"The size of the fixed area (also referred to as the fixed SGA) for the database instance, in bytes.",
Instance_Stats,sga_free_memory,number,"The total amount of free memory in the database instance SGA, in bytes.",
Instance_Stats,sga_library_cache_size,number,"The total library cache size for the database instance, in bytes.",
Instance_Stats,sga_redo_log_buffer_size,number,"The total size of the redo log buffer for the database instance, in bytes.",
Instance_Stats,sga_shared_pool_size,number,"The total size of the shared pool for this database instance, in bytes.",
Instance_Stats,sga_sql_area_size,number,"The total size of the SQL area for this database instance, in bytes.",
Instance_Stats,start_time,time,The total amount of uptime for the database instance.,
Instance_Stats,tablespace_used,string,"The total amount of tablespace used for the database instance, in bytes.",
Session_Info,buffer_cache_hit_ratio,number,The percentage of logical reads from the buffer during the session (1-physical reads/session logical reads*100).,
Session_Info,commits,number,The number of commits per second performed by the user associated with the session.,
Session_Info,cpu_used,number,The number of CPU centiseconds used by the session. Divide this value by 100 to get the CPU seconds.,
Session_Info,cursor,number,The number of the cursor currently in use by the session.,
Session_Info,elapsed_time,number,"The total amount of time elapsed since the user started the session by logging into the database server, in seconds.",
Session_Info,logical_reads,number,The total number of consistent gets and database block gets performed during the session.,
Session_Info,machine,string,The name of the logical host associated with the database instance.,
Session_Info,memory_sorts,number,The total number of memory sorts performed during the session.,
Session_Info,physical_reads,number,The total number of physical reads performed during the session.,
Session_Info,seconds_in_wait,number,"The description of seconds_in_wait depends on the value of wait_time. If wait_time = 0, seconds_in_wait is the number of seconds spent in the current wait condition. If wait_time has a nonzero value, seconds_in_wait is the number of seconds that have elapsed since the start of the last wait. You can get the active seconds that have elapsed since the last wait ended by calculating seconds_in_wait - wait_time / 100.",
Session_Info,session_id,string,The unique id that identifies the session.,
Session_Info,session_status,string,The current status of the session.,"prescribed values:Online, Offline."
Session_Info,table_scans,number,Number of table scans performed during the session.,
Session_Info,wait_state,string,Provides the current wait state for the session. Can indicate that the session is currently waiting or provide information about the session's last wait.,"prescribed values:WAITING (the session is currently waiting), WAITED UNKNOWN (the duration of the last session wait is unknown), WAITED SHORT TIME (the last session wait was < 1/100th of a second), WAITED KNOWN TIME (the wait_time is the duration of the last session wait)."
Session_Info,wait_time,number,"When wait_time = 0, the session is waiting. When wait_time has a nonzero value, it is displaying the last wait time for the session.",
Lock_Info,last_call_minute,number,"Represents the amount of time elapsed since the session_status changed to its current status. The definition of this field depends on the session_status value. If session_status = ONLINE, the last_call_minute value represents the time elapsed since the session became active. If session_status = OFFLINE, the last_call_minute value represents the time elapsed since the session became inactive.",
Lock_Info,lock_mode,string,The mode of the lock on the object.,
Lock_Info,lock_session_id,string,The session identifier of the locked object.,
Lock_Info,logon_time,number,The database logon time for the session.,
Lock_Info,obj_name,string,The name of the locked object.,
Lock_Info,os_pid,string,The process identifier for the operating system.,
Lock_Info,serial_num,string,The serial number of the object.,
Database_Query,query,string,The full database query.,
Database_Query,query_id,string,The identifier for the database query.,
Database_Query,query_time,time,The time the system initiated the database query.,
Database_Query,records_affected,number,The number of records affected by the database query.,
Tablespace,free_bytes,number,"The total amount of free space in the tablespace, in bytes.",
Tablespace,tablespace_name,string,The name of the tablespace.,
Tablespace,tablespace_reads,number,The number of tablespace reads carried out by the query.,
Tablespace,tablespace_status,string,The status of the tablespace.,"prescribed values:Offline, Online, Read Only"
Tablespace,tablespace_writes,number,The number of tablespace writes carried out by the query.,
Query_Stats,indexes_hit,string,The names of the indexes hit by the database query.,
Query_Stats,query_plan_hit,string,The name of the query plan hit by the query.,
Query_Stats,stored_procedures_called,string,The names of the stored procedures called by the query.,
Query_Stats,tables_hit,string,The names of the tables hit by the query.,
All_Email,action,string,Action taken by the reporting device.,"recommended
required for pytest-splunk-addon
prescribed values:delivered, blocked, quarantined, deleted"
All_Email,delay,number,Total sending delay in milliseconds.,
All_Email,dest,string,"The endpoint system to which the message was delivered. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
All_Email,dest_bunit,string,The business unit of the endpoint system to which the message was delivered. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,dest_category,string,The category of the endpoint system to which the message was delivered. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,dest_priority,string,The priority of the endpoint system to which the message was delivered. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,duration,number,"The amount of time for the completion of the messaging event, in seconds.",
All_Email,file_hash,string,"The hashes for the files attached to the message, if any exist.",
All_Email,file_name,string,"The names of the files attached to the message, if any exist.",
All_Email,file_size,number,"The size of the files attached the message, in bytes.",
All_Email,internal_message_id,string,Host-specific unique message identifier.,"required for pytest-splunk-addon
other:Such as aid in sendmail, IMI in Domino, Internal-Message-ID in Exchange, and MID in Ironport)."
All_Email,message_id,string,The globally-unique message identifier.,required for pytest-splunk-addon
All_Email,message_info,string,Additional information about the message.,
All_Email,orig_dest,string,The original destination host of the message. The message destination host can change when a message is relayed or bounced.,
All_Email,orig_recipient,string,The original recipient of the message. The message recipient can change when the original email address is an alias and has to be resolved to the actual recipient.,
All_Email,orig_src,string,The original source of the message.,
All_Email,process,string,The name of the email executable that carries out the message transaction.,"other:sendmail, postfix, or the name of an email client"
All_Email,process_id,number,The numeric identifier of the process invoked to send the message.,
All_Email,protocol,string,"The email protocol involved, such as SMTP or RPC.","required for pytest-splunk-addon
prescribed values:smtp, imap, pop3, mapi"
All_Email,recipient,string,A field listing individual recipient email addresses.,"recommended
required for pytest-splunk-addon
other:recipient=""foo@splunk.com"", recipient=""bar@splunk.com"""
All_Email,recipient_count,number,The total number of intended message recipients.,required for pytest-splunk-addon
All_Email,recipient_domain,string,The domain name contained within the recipient email addresses.,recommended
All_Email,recipient_status,string,"The recipient delivery status, if available.",
All_Email,response_time,number,"The amount of time it took to receive a response in the messaging event, in seconds.",
All_Email,retries,number,"The number of times that the message was automatically resent because it was bounced back, or a similar transmission error condition.",
All_Email,return_addr,string,The return address for the message.,
All_Email,size,number,"The size of the message, in bytes.",
All_Email,src,string,"The system that sent the message. You can alias this from more specific fields, such as src_host, src_ip, or src_name.","recommended
required for pytest-splunk-addon"
All_Email,src_bunit,string,The business unit of the system that sent the message. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,src_category,string,The category of the system that sent the message. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,src_priority,string,The priority of the system that sent the message. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,src_user,string,The email address of the message sender.,"recommended
required for pytest-splunk-addon"
All_Email,src_user_bunit,string,The business unit of the message sender. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,src_user_category,string,The category of the message sender. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,src_user_domain,string,The domain name contained within the email address of the message sender.,recommended
All_Email,src_user_priority,string,The priority of the message sender. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,status_code,string,The status code associated with the message.,
All_Email,subject,string,The subject of the message.,
All_Email,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Email,url,string,"The URL associated with the message, if any.",
All_Email,user,string,"The user context for the process. This is not the email address for the sender. For that, look at the src_user field.",required for pytest-splunk-addon
All_Email,user_bunit,string,The business unit of the user context for the process. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,user_category,string,The category of the user context for the process. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,user_priority,string,The priority of the user context for the process. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Email,vendor_product,string,The vendor and product of the email server used for the email transaction. This field can be automatically populated by vendor and product fields in your data.,recommended
All_Email,xdelay,string,Extended delay information for the message transaction. May contain details of all the delays from all the servers in the message transmission chain.,
All_Email,xref,string,An external reference. Can contain message IDs or recipient addresses from related messages.,
Filtering,filter_action,string,The status produced by the filter.,"other:accepted, rejected, dropped"
Filtering,filter_score,number,Numeric indicator assigned to specific emails by an email filter.,
Filtering,signature,string,The name of the filter applied.,recommended
Filtering,signature_extra,string,Any additional information about the filter.,
Filtering,signature_id,string,The id associated with the filter name.,
Ports,creation_time,timestamp,The time at which the network port started listening on the endpoint.,
Ports,dest,string,"The endpoint on which the port is listening.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon"
Ports,dest_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,dest_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,dest_port,number,"Network port listening on the endpoint, such as 53.","recommended
required for pytest-splunk-addon"
Ports,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,dest_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,dest_should_timesync,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,dest_should_update,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,process_guid,string,The globally unique identifier of the process assigned by the vendor_product.,
Ports,process_id,string,The numeric identifier of the process assigned by the operating system.,
Ports,src,string,"The ""remote"" system connected to the listening port (if applicable).
Expression: if(isnull(src) OR src=\""\"",\""unknown\"",src)","recommended
required for pytest-splunk-addon"
Ports,src_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,src_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,src_port,number,"The ""remote"" port connected to the listening port (if applicable).
Expression: if(isnum(src_port),src_port,0)","recommended
required for pytest-splunk-addon"
Ports,src_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,src_should_timesync,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,src_should_update,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,state,string,"The status of the listening port, such as established, listening, etc.",required for pytest-splunk-addon
Ports,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Ports,transport,string,"The network transport protocol associated with the listening port, such as tcp, udp, etc.""","recommended
required for pytest-splunk-addon"
Ports,transport_dest_port,string,"Calculated as transport/dest_port, such as tcp/53.",
Ports,user,string,"The user account associated with the listening port.
Expression: if(isnull(user) OR user=\""\"",\""unknown\"",user)",recommended
Ports,user_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Ports,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,action,string,"The action taken by the endpoint, such as allowed, blocked, deferred.",required for pytest-splunk-addon
Processes,cpu_load_percent,number,CPU load consumed by the process (in percent).,
Processes,dest,string,"The endpoint for which the process was spawned.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon"
Processes,dest_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,dest_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,dest_is_expected,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Processes,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,dest_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,dest_should_timesync,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,dest_should_update,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,mem_used,number,Memory used by the process (in bytes).,
Processes,original_file_name,string,"Original name of the file, not including path. Sometimes this field is similar to process name but the two do not always match, such as process_name=pwsh and original_file_name=powershell.exe to detect renamed instances of any process executing.",recommended
Processes,os,string,"The operating system of the resource, such as Microsoft Windows Server 2008r2.",
Processes,parent_process,string,"The full command string of the parent process.
Expression: if(isnull(parent_process) OR parent_process=\""\"",\""unknown\"",
parent_process)",recommended
Processes,parent_process_exec,string,The executable name of the parent process.,
Processes,parent_process_id,number,The numeric identifier of the parent process assigned by the operating system.,required for pytest-splunk-addon
Processes,parent_process_guid,string,The globally unique identifier of the parent process assigned by the vendor_product.,
Processes,parent_process_name,string,"The friendly name of the parent process, such as notepad.exe.
Expression: case(isnotnull(parent_process_name) AND parent_process_name!=\""\"",parent_process_name,
isnotnull(parent_process) AND parent_process!=\""\"",replace(parent_process,
\""^\\s*([^\\s]+).*\"",\""\\1\""),1=1,\""unknown\"")""","recommended
required for pytest-splunk-addon"
Processes,parent_process_path,string,"The file path of the parent process, such as C:\Windows\System32\notepad.exe.",required for pytest-splunk-addon
Processes,process,string,"The full command string of the spawned process. Such as C:\\WINDOWS\\system32\\cmd.exe \/c \""\""C:\\Program Files\\SplunkUniversalForwarder\\etc\\system\\bin\\powershell.cmd\"" --scheme\"""". There is a limit of 2048 characters.
Expression: if(isnull(process) OR process=\""\"",\""unknown\"",process)","recommended
required for pytest-splunk-addon"
Processes,process_current_directory,string,The current working directory used to spawn the process.,
Processes,process_exec,string,"The executable name of the process, such as notepad.exe. Sometimes this is similar to process_name, such as notepad. However in malicious scenarios, such as Fruitfly, the process_exec is Perl while the process_name is Java.",required for pytest-splunk-addon
Processes,process_hash,string,"The digests of the parent process, such as <md5>, <sha1>, etc.",
Processes,process_guid,string,The globally unique identifier of the process assigned by the vendor_product.,
Processes,process_id,number,The numeric identifier of the process assigned by the operating system.,required for pytest-splunk-addon
Processes,process_integrity_level,string,The Windows integrity level of the process.,"prescribed values:system, high, medium, low, untrusted"
Processes,process_name,string,"The friendly name of the process, such as notepad.exe. Sometimes this is similar to process_exec, such as notepad.exe. However in malicious scenarios, such as Fruitfly, the process_exec is Perl while the process_name is Java.
Expression: case(isnotnull(process_name) AND process_name!=\""\"",process_name,isnotnull
(process) AND process!=\""\"",replace(process,\""^\\s*([^\\s]+).*\"",\""\\1\""),1=1,\""unknown\"")","recommended
required for pytest-splunk-addon"
Processes,process_path,string,"The file path of the process, such as C:\Windows\System32\notepad.exe.",required for pytest-splunk-addon
Processes,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Processes,user,string,"The user account that spawned the process.
Expression: if(isnull(user) OR user=\""\"",\""unknown\"",user)","recommended
required for pytest-splunk-addon"
Processes,user_id,string,The unique identifier of the user account which spawned the process.,
Processes,user_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Processes,vendor_product,string,"The vendor and product name of the Endpoint solution that reported the event, such as Carbon Black Cb Response. This field can be automatically populated by vendor and product fields in your data.""
Expression: case(isnotnull(vendor_product),vendor_product,
isnotnull(vendor) AND vendor!=\""unknown\"" AND isnotnull(product) AND product!=\""unknown\"",vendor.\"" \"".product,isnotnull(vendor) AND vendor!=\""unknown\"" AND (isnull(product) OR product=\""unknown\""),vendor.\"" unknown\"",(isnull(vendor) OR vendor=\""unknown\"") AND isnotnull(product) AND product!=\""unknown\"",\""unknown \"".product,isnotnull(sourcetype),sourcetype,
1=1,\""unknown\"")",recommended
Services,description,string,The description of the service.,
Services,dest,string,"The endpoint for which the service is installed.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon"
Services,dest_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,dest_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,dest_is_expected,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Services,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,dest_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,dest_should_timesync,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,dest_should_update,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,process_guid,string,The globally unique identifier of the process assigned by the vendor_product.,
Services,process_id,string,The numeric identifier of the process assigned by the operating system.,
Services,service,string,"The full service name.
Expression: if(isnull(service) OR service=\""\"",\""unknown\"",service)","recommended
required for pytest-splunk-addon"
Services,service_dll,string,The dynamic link library associated with the service.,
Services,service_dll_path,string,"The file path to the dynamic link library assocatied with the service, such as C:\Windows\System32\comdlg32.dll.",
Services,service_dll_hash,string,"The digests of the dynamic link library associated with the service, such as <md5>, <sha1>, etc.",
Services,service_dll_signature_exists,boolean,Whether or not the dynamic link library associated with the service has a digitally signed signature.,
Services,service_dll_signature_verified,boolean,Whether or not the dynamic link library associated with the service has had its digitally signed signature verified.,
Services,service_exec,string,The executable name of the service.,
Services,service_hash,string,"The digest(s) of the service, such as <md5>, <sha1>, etc.",
Services,service_id,string,"The unique identifier of the service assigned by the operating system.
Expression: if(isnull(service_id) OR service_id=\""\"",\""unknown\"",service_id)",recommended
Services,service_name,string,"The friendly service name.
Expression: if(isnull(service_name) OR service_name=\""\"",\""unknown\"",service_name)","recommended
required for pytest-splunk-addon"
Services,service_path,string,"The file path of the service, such as C:\WINDOWS\system32\svchost.exe.",required for pytest-splunk-addon
Services,service_signature_exists,boolean,Whether or not the service has a digitally signed signature.,
Services,service_signature_verified,boolean,Whether or not the service has had its digitally signed signature verified.,
Services,start_mode,string,"The start mode for the service.
Expression: if(isnull(start_mode) OR start_mode=\""\"",\""unknown\"",start_mode)","recommended
required for pytest-splunk-addon
prescribed values:disabled, manual, auto"
Services,status,string,"The status of the service.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon
prescribed values:critical, started, stopped, warning"
Services,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Services,user,string,"The user account associated with the service.
Expression: if(isnull(user) OR user=\""\"",\""unknown\"",user)","recommended
required for pytest-splunk-addon"
Services,user_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Services,vendor_product,string,"The vendor and product name of the Endpoint solution that reported the event, such as Carbon Black Cb Response. This field can be automatically populated by vendor and product fields in your data.
Expression: case(isnotnull(vendor_product),vendor_product,
isnotnull(vendor) AND vendor!=\""unknown\"" AND isnotnull(product) AND product!=\""unknown\"",vendor.\"" \"".product,isnotnull(vendor) AND vendor!=\""unknown\"" AND (isnull(product) OR product=\""unknown\""),vendor.\"" unknown\"",(isnull(vendor) OR vendor=\""unknown\"") AND isnotnull(product) AND product!=\""unknown\"",\""unknown \"".product,isnotnull(sourcetype),sourcetype,
1=1,\""unknown\"")",recommended
Filesystem,action,string,"The action performed on the resource.
Expression: if(isnull(action) OR action=\""\"",\""unknown\"",action)","recommended
required for pytest-splunk-addon
prescribed values:acl_modified, created, deleted, modified, read"
Filesystem,dest,string,"The endpoint pertaining to the filesystem activity.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon"
Filesystem,dest_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,dest_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,dest_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,dest_should_timesync,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,dest_should_update,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,file_access_time,timestamp,The time that the file (the object of the event) was accessed.,recommended
Filesystem,file_create_time,timestamp,The time that the file (the object of the event) was created.,recommended
Filesystem,file_hash,string,"A cryptographic identifier assigned to the file object affected by the event.
Expression: if(isnull(file_hash) OR file_hash=\""\"",\""unknown\"",file_hash)",recommended
Filesystem,file_modify_time,timestamp,The time that the file (the object of the event) was altered.,recommended
Filesystem,file_name,string,"The name of the file, such as notepad.exe.
Expression: if(isnull(file_name) OR file_name=\""\"",\""unknown\"",file_name","recommended
required for pytest-splunk-addon"
Filesystem,file_path,string,"The path of the file, such as C:\Windows\System32\notepad.exe.
Expression: if(isnull(file_path) OR file_path=\""\"",\""unknown\"",file_path)","recommended
required for pytest-splunk-addon"
Filesystem,file_acl,string,"Access controls associated with the file affected by the event.
Expression: if(isnull(file_acl) OR file_acl=\""\"",\""unknown\"",file_acl)",recommended
Filesystem,file_size,string,"The size of the file that is the object of the event, in kilobytes.
Expression: if(isnum(file_size),file_size,null())",recommended
Filesystem,image,string,The binary file path or name that is tied to a process ID (PID) in events such as process creation or termination.,Optional
Filesystem,process_guid,string,The globally unique identifier of the process assigned by the vendor_product.,
Filesystem,process_id,string,The numeric identifier of the process assigned by the operating system.,
Filesystem,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Filesystem,user,string,"The user account associated with the filesystem access.
Expression: if(isnull(user) OR user=\""\"",\""unknown\"",user)","recommended
required for pytest-splunk-addon"
Filesystem,user_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Filesystem,vendor_product,string,"The vendor and product name of the Endpoint solution that reported the event, such as Carbon Black Cb Response. This field can be automatically populated by vendor and product fields in your data.
Expression: case(isnotnull(vendor_product),vendor_product,
isnotnull(vendor) AND vendor!=\""unknown\"" AND isnotnull(product) AND product!=\""unknown\"",vendor.\"" \"".product,isnotnull(vendor) AND vendor!=\""unknown\"" AND (isnull(product) OR product=\""unknown\""),vendor.\"" unknown\"",(isnull(vendor) OR vendor=\""unknown\"") AND isnotnull(product) AND product!=\""unknown\"",\""unknown \"".product,isnotnull(sourcetype),sourcetype,
1=1,\""unknown\"")",recommended
Registry,action,string,"The action performed on the resource.
Expression: if(isnull(action) OR action=\""\"",\""unknown\"",action)","recommended
required for pytest-splunk-addon
prescribed values:created, deleted, modified, read"
Registry,dest,string,"The endpoint pertaining to the registry events.
Expression: if(isnull(dest) OR dest=\""\"",\""unknown\"",dest)","recommended
required for pytest-splunk-addon"
Registry,dest_bunit,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,dest_category,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,dest_priority,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,dest_requires_av,boolean,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,dest_should_timesync,boolean,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,dest_should_update,boolean,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,image,string,The binary file path or name that is tied to a process ID (PID) in events such as process creation or termination.,Optional
Registry,process_guid,string,The globally unique identifier of the process assigned by the vendor_product.,
Registry,process_id,string,The numeric identifier of the process assigned by the operating system.,
Registry,registry_hive,string,"The logical grouping of registry keys, subkeys, and values.","required for pytest-splunk-addon
prescribed values:HKEY_CURRENT_CONFIG, HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE\\SAM, HKEY_LOCAL_MACHINE\\Security, HKEY_LOCAL_MACHINE\\Software, HKEY_LOCAL_MACHINE\\System, HKEY_USERS\\.DEFAULT"
Registry,registry_path,string,"The path to the registry value, such as \win\directory\directory2\{676235CD-B656-42D5-B737-49856E97D072}\PrinterDriverData.
Expression: if(isnull(registry_path) OR registry_path=\""\"",\""unknown\"",registry_path)","recommended
required for pytest-splunk-addon"
Registry,registry_key_name,string,"The name of the registry key, such as PrinterDriverData.
Expression: if(isnull(registry_key_name) OR registry_key_name=\""\"",\""unknown\"",
registry_key_name)","recommended
required for pytest-splunk-addon"
Registry,registry_value_data,string,"The unaltered registry value.
Expression: if(isnull(registry_value_data) OR registry_value_data=\""\"",\""unknown\"",
registry_value_data)","recommended
required for pytest-splunk-addon"
Registry,registry_value_name,string,"The name of the registry value.
Expression: if(isnull(registry_value_name) OR registry_value_name=\""\"",\""unknown\"",
registry_value_name)","recommended
required for pytest-splunk-addon"
Registry,registry_value_text,string,The textual representation of registry_value_data (if applicable).,required for pytest-splunk-addon
Registry,registry_value_type,string,"The type of the registry value.
Expression: if(isnull(registry_value_type) OR registry_value_type=\""\"",\""unknown\"",
registry_value_type)","recommended
required for pytest-splunk-addon
prescribed values:REG_BINARY, REG_DWORD, REG_DWORD_LITTLE_ENDIAN, REG_DWORD_BIG_ENDIAN, REG_EXPAND_SZ, REG_LINK, REG_MULTI_SZ, REG_NONE, REG_QWORD, REG_QWORD_LITTLE_ENDIAN, REG_SZ"
Registry,status,string,The outcome of the registry action.,"required for pytest-splunk-addon
prescribed values:failure, success"
Registry,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Registry,user,string,"The user account associated with the registry access.
Expression: if(isnull(user) OR user=\""\"",\""unknown\"",user)","recommended
required for pytest-splunk-addon"
Registry,user_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Registry,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Registry,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Registry,vendor_product,string,"The vendor and product name of the Endpoint solution that reported the event, such as Carbon Black Cb Response. This field can be automatically populated by vendor and product fields in your data.
Expression: case(isnotnull(vendor_product),vendor_product,
isnotnull(vendor) AND vendor!=\""unknown\"" AND isnotnull(product) AND product!=\""unknown\"",vendor.\"" \"".product,isnotnull(vendor) AND vendor!=\""unknown\"" AND (isnull(product) OR product=\""unknown\""),vendor.\"" unknown\"",(isnull(vendor) OR vendor=\""unknown\"") AND isnotnull(product) AND product!=\""unknown\"",\""unknown \"".product,isnotnull(sourcetype),sourcetype,
1=1,\""unknown\"")",recommended
Signatures,dest,string,System affected by the signature.,
Signatures,dest_bunit,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Signatures,dest_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Signatures,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this fields when writing add-ons.,
Signatures,signature,string,The human readable event name.,
Signatures,signature_id,string,The event name identifier (as supplied by the vendor).,
Signatures,tag,string,This automatically generated field is used to access tags from within data models. Add-on builders do not need to populate it.,
Signatures_vendor_product,vendor_product,string,"The vendor and product name of the technology that reported the event, such as Carbon Black Cb Response. This field can be automatically populated by vendor and product fields in your data.Expression:case(isnotnull(vendor_product),vendor_product,
isnotnull(vendor) AND vendor!=\""unknown\"" AND isnotnull(product) AND product!=\""unknown\"",vendor.\"" \"".product,isnotnull(vendor) AND vendor!=\""unknown\"" AND (isnull(product) OR product=\""unknown\""),vendor.\"" unknown\"",(isnull(vendor) OR vendor=\""unknown\"") AND isnotnull(product) AND product!=\""unknown\"",\""unknown \"".product,isnotnull(sourcetype),sourcetype,
1=1,\""unknown\"")""",recommended
All_Interprocess_Messaging,dest,string,"The destination of the message. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.",
All_Interprocess_Messaging,dest_bunit,string,The business unit of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Interprocess_Messaging,dest_category,string,The type of message destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,"prescribed values:queue, topic"
All_Interprocess_Messaging,dest_priority,string,The priority of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Interprocess_Messaging,duration,number,The number of seconds from message call to message response. Can be derived by getting the difference between the request_sent_time and the message_received_time.,
All_Interprocess_Messaging,endpoint,string,The endpoint that the message accessed during the RPC (remote procedure call) transaction.,
All_Interprocess_Messaging,endpoint_version,string,"The version of the endpoint accessed during the RPC (remote procedure call) transaction, such as 1.0 or 1.22.",
All_Interprocess_Messaging,message,string,A command or reference that an RPC (remote procedure call) reads or responds to.,
All_Interprocess_Messaging,message_consumed_time,time,The time that the RPC (remote procedure call) read the message and was prepared to take some sort of action.,
All_Interprocess_Messaging,message_correlation_id,string,The message correlation identification value.,
All_Interprocess_Messaging,message_delivered_time,time,The time that the message producer sent the message.,
All_Interprocess_Messaging,message_delivery_mode,string,"The message delivery mode. Possible values depend on the type of message-oriented middleware (MOM) solution in use. They can be words like Transient (meaning the message is stored in memory and is lost if the server dies or restarts) or Persistent (meaning the message is stored both in memory and on disk and is preserved if the server dies or restarts). They can also be numbers like 1, 2, and so on.",
All_Interprocess_Messaging,message_expiration_time,time,The time that the message expired.,
All_Interprocess_Messaging,message_id,string,The message identification.,
All_Interprocess_Messaging,message_priority,string,"The priority of the message. Important jobs that the message queue should answer no matter what receive a higher message_priority than other jobs, ensuring they are completed before the others.",
All_Interprocess_Messaging,message_properties,string,An arbitrary list of message properties. The set of properties displayed depends on the message-oriented middleware (MOM) solution that you are using.,
All_Interprocess_Messaging,message_received_time,time,The time that the message was received by a message-oriented middleware (MOM) solution.,
All_Interprocess_Messaging,message_redelivered,boolean,Indicates whether or not the message was redelivered.,
All_Interprocess_Messaging,message_reply_dest,string,The name of the destination for replies to the message.,
All_Interprocess_Messaging,message_type,string,"The type of message, such as call or reply.",
All_Interprocess_Messaging,parameters,string,Arguments that have been passed to an endpoint by a REST call or something similar. A sample parameter could be something like foo=bar.,
All_Interprocess_Messaging,payload,string,The message payload.,
All_Interprocess_Messaging,payload_type,string,"The type of payload in the message. The payload type can be text (such as json, xml, and raw) or binary (such as compressed, object, encrypted, and image).",
All_Interprocess_Messaging,request_payload,string,The content of the message request.,
All_Interprocess_Messaging,request_payload_type,string,"The type of payload in the message request. The payload type can be text (such as json, xml, and raw) or binary (such as compressed, object, encrypted, and image).",
All_Interprocess_Messaging,request_sent_time,time,The time that the message request was sent.,
All_Interprocess_Messaging,response_code,string,The response status code sent by the receiving server. Ranges between 200 and 404.,
All_Interprocess_Messaging,response_payload_type,string,"The type of payload in the message response. The payload type can be text (such as json, xml, and raw) or binary (such as compressed, object, encrypted, and image).",
All_Interprocess_Messaging,response_received_time,time,The time that the message response was received.,
All_Interprocess_Messaging,response_time,number,"The amount of time it took to receive a response, in seconds.",
All_Interprocess_Messaging,return_message,string,The response status message sent by the message server.,
All_Interprocess_Messaging,rpc_protocol,string,"The protocol that the message server uses for remote procedure calls (RPC). Possible values include HTTP REST, SOAP, and EJB.",
All_Interprocess_Messaging,status,boolean,The status of the message response.,"prescribed values:pass, fail"
All_Interprocess_Messaging,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
IDS_Attacks,action,string,The action taken by the intrusion detection system (IDS).,"required for pytest-splunk-addon
prescribed values:allowed, blocked"
IDS_Attacks,category,string,"The vendor-provided category of the triggered signature, such as spyware.This field is a string. Use a category_id field (not included in this data model) for category ID fields that are integer data types.","recommended
required for pytest-splunk-addon"
IDS_Attacks,dest,string,"The destination of the attack detected by the intrusion detection system (IDS). You can alias this from more specific fields not included in this data model, such as dest_host, dest_ip, or dest_name.",recommended
IDS_Attacks,dest_port,number,The destination port of the intrusion.,
IDS_Attacks,dvc,string,"The device that detected the intrusion event. You can alias this from more specific fields not included in this data model, such as dvc_host, dvc_ip, or dvc_name.","recommended
required for pytest-splunk-addon"
IDS_Attacks,file_hash,string,A cryptographic identifier assigned to the file object affected by the event.,
IDS_Attacks,file_name,string,"The name of the file, such as notepad.exe.",
IDS_Attacks,file_path,string,"The path of the file, such as C:\\Windows\\System32\\notepad.exe.",
IDS_Attacks,ids_type,string,The type of IDS that generated the event.,"recommended
required for pytest-splunk-addon
prescribed values:network, host, application, wireless"
IDS_Attacks,severity,string,"The severity of the network protection event.This field is a string. Use a severity_id field (not included in this data model) for severity ID fields that are integer data types. Also, specific values are required for this field. Use vendor_severity for the vendor's own human readable severity strings, such as Good, Bad, and Really Bad.","recommended
required for pytest-splunk-addon
prescribed values:critical, high, medium, low, informational"
IDS_Attacks,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
IDS_Attacks,signature,string,"The name of the intrusion detected on the client (the src), such as PlugAndPlay_BO and JavaScript_Obfuscation_Fre.","recommended
required for pytest-splunk-addon"
IDS_Attacks,signature_id,string,The unique identifier or event code of the event signature.,
IDS_Attacks,src,string,"The source involved in the attack detected by the IDS. You can alias this from more specific fields not included in this data model, such as src_host, src_ip, or src_name.",recommended
IDS_Attacks,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
IDS_Attacks,transport,string,"The OSI layer 4 (transport) or internet layer protocol of the intrusion, in lower case.","recommended
required for pytest-splunk-addon
prescribed values:

icmp,
tcp,
udp"
IDS_Attacks,user,string,The user involved with the intrusion detection event.,recommended
IDS_Attacks,vendor_product,string,"The vendor and product name of the IDS or IPS system that detected the vulnerability, such as HP Tipping Point. This field can be automatically populated by vendor and product fields in your data.",recommended
JVM,jvm_description,string,A description field provided in some data sources.,
JVM,tag,string,This automatically generated field is used to access tags from within datamodels. Add-on builders do not need to populate it.,
Threading,cm_enabled,boolean,Indicates whether thread contention monitoring is enabled.,"prescribed values:true, false, 1, 0"
Threading,cm_supported,boolean,Indicates whether the JVM supports thread contention monitoring.,"prescribed values:true, false, 1, 0"
Threading,cpu_time_enabled,boolean,Indicates whether thread CPU time measurement is enabled.,"prescribed values:true, false, 1, 0"
Threading,cpu_time_supported,boolean,Indicates whether the Java virtual machine supports CPU time measurement for the current thread.,"prescribed values:true, false, 1, 0"
Threading,current_cpu_time,number,"CPU-space time taken by the JVM, in seconds.",
Threading,current_user_time,number,"User-space time taken by the JVM, in seconds.",
Threading,daemon_thread_count,number,The JVM's current daemon count.,
Threading,omu_supported,boolean,Indicates whether the JVM supports monitoring of object monitor usage.,"prescribed values:true, false, 1, 0"
Threading,peak_thread_count,number,The JVM's peak thread count.,
Threading,synch_supported,boolean,Indicates whether the JVM supports monitoring of ownable synchronizer usage.,"prescribed values:true, false, 1, 0"
Threading,thread_count,number,The JVM's current thread count.,
Threading,threads_started,number,The total number of threads started in the JVM.,
Runtime,process_name,string,Process name of the JVM process.,
Runtime,start_time,timestamp,Start time of the JVM process.,
Runtime,uptime,number,"Uptime of the JVM process, in seconds.",
Runtime,vendor_product,string,The JVM product or service. This field can be automatically populated by the the vendor and product fields in your raw data.,
Runtime,version,string,Version of the JVM.,
OS,committed_memory,number,"Amount of memory committed to the JVM, in bytes.",
OS,cpu_time,number,"Amount of CPU time taken by the JVM, in seconds.",
OS,free_physical_memory,number,"Amount of free physical memory remaining to the JVM, in bytes.",
OS,free_swap,number,"Amount of free swap memory remaining to the JVM, in bytes.",
OS,max_file_descriptors,number,Maximum file descriptors available to the JVM.,
OS,open_file_descriptors,number,Number of file descriptors opened by the JVM.,
OS,os,string,OS that the JVM is running on.,
OS,os_architecture,string,OS architecture that the JVM is running on.,
OS,os_version,string,OS version that the JVM is running on.,
OS,physical_memory,number,"Physical memory available to the OS that the JVM is running on, in bytes.",
OS,swap_space,number,"Swap memory space available to the OS that the JVM is running on, in bytes.",
OS,system_load,number,System load of the OS that the JVM is running on.,
OS,total_processors,number,Total processor cores available to the OS that the JVM is running on.,
Compilation,compilation_time,number,"Time taken by JIT compilation, in seconds.",
Classloading,current_loaded,number,The current count of classes loaded in the JVM.,
Classloading,total_loaded,number,The total count of classes loaded in the JVM.,
Classloading,total_unloaded,number,The total count of classes unloaded from the JVM.,
Memory,heap_committed,number,"Committed amount of heap memory used by the JVM, in bytes.",
Memory,heap_initial,number,"Initial amount of heap memory used by the JVM, in bytes.",
Memory,heap_max,number,"Maximum amount of heap memory used by the JVM, in bytes.",
Memory,heap_used,number,"Heap memory used by the JVM, in bytes.",
Memory,non_heap_committed,number,"Committed amount of non-heap memory used by the JVM, in bytes.",
Memory,non_heap_initial,number,"Initial amount of non-heap memory used by the JVM, in bytes.",
Memory,non_heap_max,number,"Maximum amount of non-heap memory used by the JVM, in bytes.",
Memory,non_heap_used,number,"Non-heap memory used by the JVM, in bytes.",
Memory,objects_pending,number,"Number of objects pending in the JVM, in bytes.",
Malware_Attacks,action,string,The action taken by the reporting device.,"recommended
required for pytest-splunk-addon
prescribed values:allowed, blocked, deferred"
Malware_Attacks,category,string,"The category of the malware event, such as keylogger or ad-supported program.Note: This is a string value. Use a category_id field for category ID fields that are integer data types (category_id fields are optional, so they are not included in this table).","recommended
required for pytest-splunk-addon"
Malware_Attacks,date,string,"The time of the malware action such as when it was blocked, allowed or deferred, as it was reported by log event.",recommended
Malware_Attacks,dest,string,"The system that was affected by the malware event. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
Malware_Attacks,file_hash,string,The hash of the file with suspected malware.,
Malware_Attacks,file_name,string,The name of the file with suspected malware.,required for pytest-splunk-addon
Malware_Attacks,file_path,string,The full file path of the file with suspected malware.,required for pytest-splunk-addon
Malware_Attacks,severity,string,"The severity of the network protection event. Note: This field is a string. Use severity_id for severity ID fields that are integer data types. Also, specific values are required for this field. Use vendor_severity for the vendor's own human readable severity strings, such as Good, Bad, and Really Bad.","recommended
prescribed values:critical, high, medium, low, informational,"
Malware_Attacks,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
Malware_Attacks,signature,string,The name of the malware infection detected on the client (the dest).Note: This is a string value. Use a signature_id field for signature ID fields that are integer data types.,"recommended
required for pytest-splunk-addon
other:such as Trojan.Vundo, Spyware.Gaobot, W32.Nimbda"
Malware_Attacks,signature_id,string,The unique identifier or event code of the event signature.,
Malware_Attacks,src,string,"The source of the event, such as a DAT file relay server. You can alias this from more specific fields, such as src_host, src_ip, or src_name.",
Malware_Attacks,src_bunit,string,The business unit of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Malware_Attacks,src_category,string,The category of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Malware_Attacks,src_priority,string,The priority of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Malware_Attacks,src_user,string,The reported sender of an email-based attack.,
Malware_Attacks,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
Malware_Attacks,user,string,The user involved in the malware event.,recommended
Malware_Attacks,url,string,A URL containing more information about the malware.,
Malware_Attacks,vendor_product,string,"The vendor and product name of the endpoint protection system, such as Symantec AntiVirus. This field can be automatically populated by vendor and product fields in your data.",recommended
Malware_Operations,dest,string,The system where the malware operations event occurred.,"recommended
required for pytest-splunk-addon"
Malware_AttacksMalware_Operations,dest_nt_domain,string,"The NT domain of the dest system, if applicable.",recommended
Malware_Operations,dest_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Malware_Operations,dest_requires_av,boolean,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
Malware_Operations,product_version,string,The product version of the malware operations product.,recommended
Malware_Operations,signature_version,string,The version of the malware signature bundle in a signature update operations event.,"recommended
required for pytest-splunk-addon"
Malware_Operations,tag,string,The tag associated with the malware operations event.,
Malware_Operations,vendor_product,string,The vendor product name of the malware operations product.,"recommended
required for pytest-splunk-addon"
DNS,additional_answer_count,number,"Number of entries in the ""additional"" section of the DNS message.",required for pytest-splunk-addon
DNS,answer,string,Resolved address for the query.,"recommended
required for pytest-splunk-addon"
DNS,answer_count,number,Number of entries in the answer section of the DNS message.,required for pytest-splunk-addon
DNS,authority_answer_count,number,Number of entries in the 'authority' section of the DNS message.,required for pytest-splunk-addon
DNS,dest,string,"The destination of the network resolution event. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
DNS,dest_bunit,string,The business unit of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DNS,dest_category,string,"The category of the network resolution target, such as email_server or SOX-compliant.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
DNS,dest_port,number,The destination port number.,recommended
DNS,dest_priority,string,"The priority of the destination, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
DNS,duration,number,"The time taken by the network resolution event, in seconds.",
DNS,message_type,string,Type of DNS message.,"recommended
required for pytest-splunk-addon
prescribed values:Query, Response"
DNS,name,string,The name of the DNS event.,
DNS,query,string,"The domain which needs to be resolved. Applies to messages of type ""Query"".","recommended
required for pytest-splunk-addon"
DNS,query_count,number,"Number of entries that appear in the ""Questions"" section of the DNS query.",required for pytest-splunk-addon
DNS,query_type,string,"The field may contain DNS OpCodes or Resource Record Type codes. For details, see the Domain Name System Parameters on the Internet Assigned Numbers Authority (IANA)  web site. If a value is not set, the DNS.record_type fieldis referenced.","required for pytest-splunk-addon
Example values: Query, IQuery, Status, Notify, Update, A, MX, NS, PTR"
DNS,record_type,string,"The DNS resource record type. For details, see the List of DNS record types on the IANA web site.","required for pytest-splunk-addon
Example values: A, DNAME, MX, NS, PTR"
DNS,reply_code,string,"The return code for the response. For details, see the Domain Name System Parameters on the Internet Assigned Numbers Authority (IANA) web site.","recommended
required for pytest-splunk-addon
prescribed values:No Error, Format Error, Server Failure, Non-Existent Domain
other: NoError, FormErr, ServFail, NXDomain, NotImp, Refused, YXDomain, YXRRSet, NotAuth, NotZone, BADVERS, BADSIG, BADKEY, BADTIME, BADMODE, BADNAME, BADALG"
DNS,reply_code_id,number,"The numerical id of a return code. For details, see the Domain Name System Parameters on the Internet Assigned Numbers Authority (IANA) web site.","recommended
required for pytest-splunk-addon
prescribed values:0, NoError, 1, FormErr,2, ServFail, 3, NXDomain,"
DNS,response_time,number,"The amount of time it took to receive a response in the network resolution event, in seconds if consistent across all data sources, if applicable.",required for pytest-splunk-addon
DNS,src,string,"The source of the network resolution event. You can alias this from more specific fields, such as src_host, src_ip, or src_name.","recommended
required for pytest-splunk-addon"
DNS,src_bunit,string,The business unit of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DNS,src_category,string,"The category of the source, such as email_server or SOX-compliant. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
DNS,src_port,number,The port number of the source.,recommended
DNS,src_priority,string,The priority of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
DNS,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
DNS,transaction_id,number,The unique numerical transaction id of the network resolution event.,required for pytest-splunk-addon
DNS,transport,string,The transport protocol used by the network resolution event.,required for pytest-splunk-addon
DNS,ttl,number,The time-to-live of the network resolution event.,recommended
DNS,vendor_product,string,"The vendor product name of the DNS server. The Splunk platform can derive this field from the fields vendor and product in the raw data, if they exist.",recommended
All_Sessions,action,string,The action taken by the reporting device.,"Required for pytest-splunk-addon
Prescribed values are:

started (for VPN session starts, and DHCP lease starts)
ended (for VPN session teardowns, and DHCP lease ends)
blocked (for the VPN session disallowed start attempts, or failed DHCP leases)"
All_Sessions,dest_bunit,string,The business unit of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,dest_category,string,The category of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,dest_dns,string,The domain name system address of the destination for a network session event.,recommended
All_Sessions,dest_ip,string,"The internal IP address allocated to the client initializing a network session. For DHCP and VPN events, this is the IP address leased to the client.","recommended
required for pytest-splunk-addon"
All_Sessions,dest_mac,string,"The internal MAC address of the network session client. For DHCP events, this is the MAC address of the client acquiring an IP address lease. For VPN events, this is the MAC address of the client initializing a network session. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.","recommended
required for pytest-splunk-addon"
All_Sessions,dest_nt_host,string,The NetBIOS name of the client initializing a network session.,recommended
All_Sessions,dest_priority,string,The priority of the destination. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,duration,number,"The amount of time for the completion of the network session event, in seconds.",
All_Sessions,response_time,number,"The amount of time it took to receive a response in the network session event, if applicable.",
All_Sessions,signature,string,An indication of the type of network session event.,"required for pytest-splunk-addon
For example: DHCPACK, DHCPNAK, DHCPRELEASE, WebVPN session started, etc2."
All_Sessions,signature_id,string,The unique identifier or event code of the event signature.,
All_Sessions,src_bunit,string,The business unit of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,src_category,string,The category of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,src_dns,string,The external domain name of the client initializing a network session. Not applicable for DHCP events.,
All_Sessions,src_ip,string,The IP address of the client initializing a network session. Not applicable for DHCP events.,
All_Sessions,src_mac,string,"The MAC address of the client initializing a network session. Not applicable for DHCP events. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.",
All_Sessions,src_nt_host,string,The NetBIOS name of the client initializing a network session. Not applicable for DHCP events.,
All_Sessions,src_priority,string,The priority of the source. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Sessions,user,string,"The user in a network session event, where applicable. For example, a VPN session or an authenticated DHCP event.","recommended
required for pytest-splunk-addon"
All_Sessions,user_bunit,string,The business unit associated with the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,user_category,string,The category of the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,user_priority,string,The priority of the user. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Sessions,vendor_product,string,"The full name of the DHCP or DNS server involved in this event, including vendor and product name. For example, Microsoft DHCP or ISC BIND. Create this field by combining the values of the vendor and product fields, if present in the events.",recommended
DHCP,lease_duration,number,"The duration of the DHCP lease, in seconds.",
DHCP,lease_scope,string,The consecutive range of possible IP addresses that the DHCP server can lease to clients on a subnet. A lease_scope typically defines a single physical subnet on your network to which DHCP services are offered.,required for pytest-splunk-addon
All_Traffic,action,string,The action taken by the network device.,"recommended
required for pytest-splunk-addon
prescribed values:allowed blocked, teardown"
All_Traffic,app,string,The application protocol of the traffic.,required for pytest-splunk-addon
All_Traffic,bytes,number,Total count of bytes handled by this device/interface (bytes_in + bytes_out).,recommended
All_Traffic,bytes_in,number,How many bytes this device/interface received.,recommended
All_Traffic,bytes_out,number,How many bytes this device/interface transmitted.,recommended
All_Traffic,channel,number,The 802.11 channel used by a wireless network.,
All_Traffic,dest,string,"The destination of the network traffic (the remote host). You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
All_Traffic,dest_bunit,string,"colspan=""2"" rowspan=""2""These fields are automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for these fields when writing add-ons.",
All_Traffic,dest_category,string,,
All_Traffic,dest_interface,string,"The interface that is listening remotely or receiving packets locally. Can also be referred to as the ""egress interface.""",
All_Traffic,dest_ip,string,The IP address of the destination.,
All_Traffic,dest_mac,string,"The destination TCP/IP layer 2 Media Access Control (MAC) address of a packet's destination, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.",
All_Traffic,dest_port,number,"The destination port of the network traffic.Note: Do not translate the values of this field to strings (tcp/80 is 80, not http). You can set up the corresponding string value in a dest_svc field by extending the data model.",recommended
All_Traffic,dest_priority,string,"The destination priority, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Traffic,dest_translated_ip,string,The NATed IPv4 or IPv6 address to which a packet has been sent.,
All_Traffic,dest_translated_port,number,"The NATed port to which a packet has been sent. Note: Do not translate the values of this field to strings (tcp/80 is 80, not http).",
All_Traffic,dest_zone,string,The network zone of the destination.,required for pytest-splunk-addon
All_Traffic,direction,string,The direction the packet is traveling.,"prescribed values:inbound, outbound"
All_Traffic,duration,number,"The amount of time for the completion of the network event, in seconds.",
All_Traffic,dvc,string,"The device that reported the traffic event. You can alias this from more specific fields, such as dvc_host, dvc_ip, or dvc_name.","recommended
required for pytest-splunk-addon"
All_Traffic,dvc_bunit,string,These fields are automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for these fields when writing add-ons.,
All_Traffic,dvc_ip,string,The ip address of the device.,
All_Traffic,dvc_mac,string,"The device TCP/IP layer 2 Media Access Control (MAC) address of a packet's destination, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field and use colons instead of dashes, spaces, or no separator.",
All_Traffic,dvc_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Traffic,dvc_zone,string,The network zone of the device.,
All_Traffic,flow_id,string,"Unique identifier for this traffic stream, such as a netflow, jflow, or cflow.",
All_Traffic,icmp_code,string,"The RFC 2780 or RFC 4443 human-readable code value of the traffic, such as Destination Unreachable or Parameter Problem . See the ICMP Type Numbers and the ICMPv6 Type Numbers.",
All_Traffic,icmp_type,number,The RFC 2780 or RFC 4443 numeric value of the traffic. See the ICMP Type Numbers and the ICMPv6 Type Numbers.,prescribed values:0 to 254
All_Traffic,packets,number,The total count of packets handled by this device/interface (packets_in + packets_out).,
All_Traffic,packets_in,number,The total count of packets received by this device/interface.,
All_Traffic,packets_out,number,The total count of packets transmitted by this device/interface.,
All_Traffic,process_id,string,The numeric identifier of the process (PID) or service generating the network traffic.,
All_Traffic,protocol,string,"The OSI layer 3 (network) protocol of the traffic observed, in lower case. For example, ip, appletalk, ipx.",
All_Traffic,protocol_version,string,Version of the OSI layer 3 protocol.,
All_Traffic,response_time,number,"The amount of time it took to receive a response in the network event, if applicable.",
All_Traffic,rule,string,"The rule name that defines the action that was taken in the event. Note: Use rule_id field for the unique ID of the rule, which is often numeric.",recommended
All_Traffic,rule_id,string,"The vendor-specific unique identifier of the rule. Examples: 0x00011f0000011f00, 0x00011f00-syn_flood.",Optional
All_Traffic,session_id,string,The session identifier. Multiple transactions build a session.,
All_Traffic,src,string,"The source of the network traffic (the client requesting the connection). You can alias this from more specific fields, such as src_host, src_ip, or src_name.","recommended
required for pytest-splunk-addon"
All_Traffic,src_bunit,string,These fields are automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for these fields when writing add-ons.,
All_Traffic,src_interface,string,"The interface that is listening locally or sending packets remotely. Can also be referred to as the ""ingress interface.""",
All_Traffic,src_ip,string,The ip address of the source.,
All_Traffic,src_mac,string,"The source TCP/IP layer 2 Media Access Control (MAC) address of a packet's destination, such as 06:10:9f:eb:8f:14. Note: Always force lower case on this field. Note: Always use colons instead of dashes, spaces, or no separator.",
All_Traffic,src_port,number,"The source port of the network traffic.Note: Do not translate the values of this field to strings (tcp/80 is 80, not http). You can set up the corresponding string value in the src_svc field.",recommended
All_Traffic,src_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Traffic,src_translated_ip,string,The NATed IPv4 or IPv6 address from which a packet has been sent..,required for pytest-splunk-addon
All_Traffic,src_translated_port,number,"The NATed port from which a packet has been sent. Note: Do not translate the values of this field to strings (tcp/80 is 80, not http).",
All_Traffic,src_zone,string,The network zone of the source.,required for pytest-splunk-addon
All_Traffic,ssid,string,The 802.11 service set identifier (ssid) assigned to a wireless session.,
All_Traffic,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Traffic,tcp_flag,string,The TCP flag(s) specified in the event.,"prescribed values:SYN, ACK, FIN, RST, URG, or PSH."
All_Traffic,transport,string,"The OSI layer 4 (transport) or internet layer protocol of the traffic observed, in lower case.","recommended
required for pytest-splunk-addon
prescribed values:icmp, tcp, udp"
All_Traffic,tos,string,The combination of source and destination IP ToS (type of service) values in the event.,
All_Traffic,ttl,number,"The ""time to live"" of a packet or diagram.",
All_Traffic,user,string,The user that requested the traffic flow.,recommended
All_Traffic,user_bunit,string,These fields are automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for these fields when writing add-ons.,
All_Traffic,user_category,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Traffic,user_priority,string,This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Traffic,vendor_account,string,"The account associated with the network traffic. The account represents the organization, or a Cloud  customer or a Cloud account.",
All_Traffic,vendor_product,string,The vendor and product of the device generating the network event. This field can be automatically populated by vendor and product fields in your data.,recommended
All_Traffic,vlan,string,The virtual local area network (VLAN) specified in the record.,
All_Traffic,wifi,string,"The wireless standard(s) in use, such as 802.11a, 802.11b, 802.11g, or 802.11n.",
All_Performance,dest,string,"The system where the event occurred, usually a facilities resource such as a rack or room. You can alias this from more specific fields in your event data, such as dest_host, dest_ip, or dest_name.",recommended
All_Performance,dest_bunit,string,The business unit of the system where the event occurred.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Performance,dest_category,string,The category of the system where the event occurred. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Performance,dest_priority,string,The priority of the system where the performance event occurred.,
All_Performance,dest_should_timesync,boolean,Indicates whether or not the system where the performance event occurred should time sync. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Performance,dest_should_update,boolean,Indicates whether or not the system where the performance event occurred should update. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Performance,hypervisor_id,string,The ID of the virtualization hypervisor.,
All_Performance,resource_type,string,"The type of facilities resource involved in the performance event, such as a rack, room, or system.",
All_Performance,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
CPU,cpu_load_mhz,number,The amount of CPU load reported by the controller in megahertz.,
CPU,cpu_load_percent,number,The amount of CPU load reported by the controller in percentage points.,recommended
CPU,cpu_time,number,The number of CPU seconds consumed by processes.,
CPU,cpu_user_percent,number,Percentage of CPU user time consumed by processes.,
Facilities,fan_speed,number,"The speed of the cooling fan in the facilities resource, in rotations per second.",
Facilities,temperature,number,"Average temperature of the facilities resource, in °C.",recommended
Memory,mem,number,"The total amount of memory capacity reported by the resource, in megabytes.",recommended
Memory,mem_committed,number,"The committed amount of memory reported by the resource, in megabytes.",
Memory,mem_free,number,"The free amount of memory reported by the resource, in megabytes.",recommended
Memory,mem_used,number,"The used amount of memory reported by the resource, in megabytes.",recommended
Memory,swap,number,"The total swap space size, in megabytes, if applicable.",
Memory,swap_free,number,"The free swap space size, in megabytes, if applicable.",
Memory,swap_used,number,"The used swap space size, in megabytes, if applicable.",
Storage,array,number,"The array that the resource is a member of, if applicable.",
Storage,blocksize,number,"Block size used by the storage resource, in kilobytes.",
Storage,cluster,string,"The cluster that the resource is a member of, if applicable.",
Storage,fd_max,number,The maximum number of available file descriptors.,
Storage,fd_used,number,The current number of open file descriptors.,
Storage,latency,number,"The latency reported by the resource, in milliseconds.",
Storage,mount,string,The mount point of a storage resource.,
Storage,parent,string,"A generic indicator of hierarchy. For instance, a disk event might include the array ID here.",
Storage,read_blocks,number,Number of blocks read.,
Storage,read_latency,number,"The latency of read operations, in milliseconds.",
Storage,read_ops,number,Number of read operations.,
Storage,storage,number,"The total amount of storage capacity reported by the resource, in megabytes.",
Storage,storage_free,number,"The free amount of storage capacity reported by the resource, in megabytes.",recommended
Storage,storage_free_percent,number,The percentage of storage capacity reported by the resource that is free.,recommended
Storage,storage_used,number,"The used amount of storage capacity reported by the resource, in megabytes.",recommended
Storage,storage_used_percent,number,The percentage of storage capacity reported by the resource that is used.,recommended
Storage,write_blocks,number,The number of blocks written by the resource.,
Storage,write_latency,number,"The latency of write operations, in milliseconds.",
Storage,write_ops,number,The total number of write operations processed by the resource.,
Network,thruput,number,"The current throughput reported by the service, in bytes.",recommended
Network,thruput_max,number,"The maximum possible throughput reported by the service, in bytes.",
OS,signature,string,"The event description signature, if available.",recommended
OS,signature_id,string,The unique identifier or event code of the event signature.,
Timesync,action,string,The result of a time sync event.,"recommended
prescribed values:success, failure"
Uptime,uptime,number,"The uptime of the compute resource, in seconds.",recommended
View_Activity,app,string,The app name which contains the view.,
View_Activity,spent,number,The amount of time spent loading the view (in milliseconds).,
View_Activity,uri,string,The uniform resource identifier of the view activity.,
View_Activity,user,string,The username of the user who accessed the view.,
View_Activity,view,string,The name of the view.,
Datamodel_Acceleration,access_count,number,The number of times the data model summary has been accessed since it was created.,
Datamodel_Acceleration,access_time,time,The timestamp of the most recent access of the data model summary.,
Datamodel_Acceleration,app,string,The application context in which the data model summary was accessed.,
Datamodel_Acceleration,buckets,number,The number of index buckets spanned by the data model acceleration summary.,
Datamodel_Acceleration,buckets_size,number,The total size of the bucket(s) spanned by the data model acceleration summary.,
Datamodel_Acceleration,complete,number,The percentage of the data model summary that is currently complete.,other:0-100
Datamodel_Acceleration,cron,string,The cron expression used to accelerate the data model.,
Datamodel_Acceleration,datamodel,string,The name of the data model accelerated.,
Datamodel_Acceleration,digest,string,A hash of the current data model constraints.,
Datamodel_Acceleration,earliest,time,The earliest time that the data model summary was accessed.,
Datamodel_Acceleration,is_inprogress,boolean,Indicates whether the data model acceleration is currently in progress.,"prescribed values:true, false, 1, 0"
Datamodel_Acceleration,last_error,string,The text of the last error reported during the data model acceleration.,
Datamodel_Acceleration,last_sid,string,The search id of the last acceleration attempt.,
Datamodel_Acceleration,latest,time,The most recent acceleration timestamp of the data model.,
Datamodel_Acceleration,mod_time,time,The timestamp of the most recent modification to the data model acceleration.,
Datamodel_Acceleration,retention,number,"The length of time that data model accelerations are retained, in seconds.",
Datamodel_Acceleration,size,number,"The amount of storage space the data model's acceleration summary takes up, in bytes.",
Datamodel_Acceleration,summary_id,string,The unique id of the data model acceleration summary.,
Search_Activity,host,string,The host on which the search occurred.,
Search_Activity,info,string,"The action of the search (granted, completed, cancelled, failed).",
Search_Activity,search,string,The search string.,
Search_Activity,search_et,string,The earliest time of the search.,
Search_Activity,search_lt,string,The latest time of the search.,
Search_Activity,search_type,string,The type of search.,
Search_Activity,source,string,The source associated with the search.,
Search_Activity,sourcetype,string,The source types included in the search.,
Search_Activity,user,string,The name of the user who ran the search.,
Scheduler_Activity,app,string,The app context in which the scheduled search was run.,
Scheduler_Activity,host,string,The host on which the scheduled search was run.,
Scheduler_Activity,savedsearch_name,string,The name of the saved search.,
Scheduler_Activity,sid,string,The search id.,
Scheduler_Activity,source,string,The source associated with the scheduled search.,
Scheduler_Activity,sourcetype,string,The source type associated with the scheduled search.,
Scheduler_Activity,splunk_server,string,The Splunk Server on which the scheduled search runs.,
Scheduler_Activity,status,string,The status of the scheduled search.,
Scheduler_Activity,user,string,The user who scheduled the search.,
Web_Service_Errors,host,string,The host on which the web service error occurred.,
Web_Service_Errors,source,string,The source where the web service error occurred.,
Web_Service_Errors,sourcetype,string,The source type associated with the web service error.,
Web_Service_Errors,event_id,string,The unique event_id for the web service error event.,
Modular_Actions,action_mode,string,"Specifies whether the action was executed as an ad hoc action or from a saved search, based on whether a search_name exists.","prescribed values:saved, adhoc"
Modular_Actions,action_status,string,"The status of the action. For example, ""success"", ""failure"", or ""pending"".",
Modular_Actions,app,string,The app ID of the app or add-on that owns the action.,
Modular_Actions,duration,number,"How long the action took to complete, in milliseconds.",
Modular_Actions,component,string,The component of the modular action script involved in the event.  Often used in conjunction with duration.,
Modular_Actions,orig_rid,string,"The rid value of a source action result, automatically added to an event if it is the product of a previously executed action.",
Modular_Actions,orig_sid,string,"The original sid value of a source action, automatically added to an event if it is the product of a previously executed action.",
Modular_Actions,rid,string,"The id associated with the result of a specific sid. By default, this is the row number of the search, starting with 0.",
Modular_Actions,search_name,string,The name of the correlation search that triggered the action. Blank for ad hoc actions.,
Modular_Actions,action_name,string,The name of the action.,
Modular_Actions,signature,string,The logging string associated with alert action introspection events.,
Modular_Actions,sid,string,"The search id, automatically assigned by splunkd.",
Modular_Actions,user,string,The user who triggered an ad hoc alert. Not relevant for actions triggered by searches.,
All_Ticket_Management,affect_dest,string,Destinations affected by the service request.,
All_Ticket_Management,comments,string,Comments about the service request.,
All_Ticket_Management,description,string,The description of the service request.,
All_Ticket_Management,dest,string,"The destination of the service request. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.",
All_Ticket_Management,dest_bunit,string,"The business unit associated with the destination user or entity of the triggering events, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Ticket_Management,dest_category,string,The category of the destination.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Ticket_Management,dest_priority,string,The priority of the destination.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Ticket_Management,priority,string,The relative priority of the service request.,
All_Ticket_Management,severity,string,The relative severity of the service request.,
All_Ticket_Management,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
All_Ticket_Management,splunk_id,string,"The unique identifier of the service request as it pertains to Splunk. For example, 14DA67E8-6084-4FA8-9568-48D05969C522@@_internal@@0533eff241db0d892509be46cd3126e30e0f6046.",
All_Ticket_Management,splunk_realm,string,"The Splunk application or use case associated with the unique identifier (splunk_id). For example, es_notable.",
All_Ticket_Management,src_user,string,"The user or entity creating or triggering the ticket, if applicable.",
All_Ticket_Management,src_user_bunit,string,"The business unit associated with the source user or entity within the triggering events, if applicable.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Ticket_Management,src_user_category,string,The category associated with the user or entity that triggered the service request.This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Ticket_Management,src_user_priority,string,The priority associated with the user or entity that triggered the service request. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.,
All_Ticket_Management,status,string,The relative status of the service request.,
All_Ticket_Management,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
All_Ticket_Management,ticket_id,string,"An identification name, code, or number for the service request.",
All_Ticket_Management,time_submitted,time,The time that the src_user submitted the service request.,
All_Ticket_Management,user,string,"The name of the user or entity that is assigned to the ticket, if applicable.",
All_Ticket_Management,user_bunit,string,"The business unit associated with the user or entity that is carrying out the service request, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Ticket_Management,user_category,string,"The category associated with the user or entity that is assigned to carry out the service request, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
All_Ticket_Management,user_priority,string,"The priority of the user or entity that is assigned to carry out the service request, if applicable. This field is automatically provided by asset and identity correlation features of applications like Splunk Enterprise Security. Do not define extractions for this field when writing add-ons.",
Change,change,string,Designation for a request for change (RFC) that is raised to modify an IT service to resolve an incident or problem.,
Incident,incident,string,"The incident that triggered the service request. Can be a rare occurrence, or something that happens more frequently. An incident that occurs on a frequent basis can also be classified as a problem.",
Problem,problem,string,"When multiple occurrences of related incidents are observed, they are collectively designated with a single problem value. Problem management differs from the process of managing an isolated incident. Often problems are managed by a specific set of staff and through a problem management process.",
Updates,dest,string,"The system that is affected by the patch change. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
Updates,dvc,string,"The device that detected the patch event, such as a patching or configuration management server. You can alias this from more specific fields, such as dvc_host, dvc_ip, or dvc_name.",required for pytest-splunk-addon
Updates,file_hash,string,The checksum of the patch package that was installed or attempted.,
Updates,file_name,string,The name of the patch package that was installed or attempted.,required for pytest-splunk-addon
Updates,severity,string,The severity associated with the patch event.,"prescribed values:critical, high, medium, low, informational"
Updates,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
Updates,signature,string,"The name of the patch requirement detected on the client (the dest), such as MS08-067 or RHBA-2013:0739.Note: This is a string value. Use signature_id for numeric indicators.","recommended
required for pytest-splunk-addon"
Updates,signature_id,int,The ID of the patch requirement detected on the client (the src).Note: Use signature for human-readable signature names.,"recommended
required for pytest-splunk-addon"
Updates,status,string,Indicates the status of a given patch requirement.,"recommended
required for pytest-splunk-addon
prescribed values:
Following are some prescribed values:


available: The patch or update is ready but not necessarily installed.
installed: The patch or update is successfully installed.
invalid: The patch or update is detected as invalid.
""restart required"": A restart is required after the patch installed.
""failure"": The installation patch or update failed to install."
Updates,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
Updates,vendor_product,string,"The vendor and product of the patch monitoring product, such as Lumension Patch Manager. This field can be automatically populated by vendor and product fields in your data.",recommended
Vulnerabilities,bugtraq,string,Corresponds to an identifier in the vulnerability database provided by the Security Focus website (searchable at http://www.securityfocus.com/).,
Vulnerabilities,category,string,"The category of the discovered vulnerability, such as DoS.Note: This field is a string. Use  category_id for numeric values. The category_id field is optional and thus is not included in the data model.","recommended
required for pytest-splunk-addon"
Vulnerabilities,cert,string,"Corresponds to an identifier in the vulnerability database provided by the US Computer Emergency Readiness Team (US-CERT, searchable at http://www.kb.cert.org/vuls/).",
Vulnerabilities,cve,string,Corresponds to an identifier provided in the Common Vulnerabilities and Exposures index (searchable at http://cve.mitre.org).,"recommended
required for pytest-splunk-addon"
Vulnerabilities,cvss,number,Numeric indicator of the common vulnerability scoring system.,required for pytest-splunk-addon
Vulnerabilities,dest,string,"The host with the discovered vulnerability. You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
Vulnerabilities,dvc,string,"The system that discovered the vulnerability. You can alias this from more specific fields, such as dvc_host, dvc_ip, or dvc_name.","recommended
required for pytest-splunk-addon"
Vulnerabilities,msft,string,Corresponds to a Microsoft Security Advisory number (http://technet.microsoft.com/en-us/security/advisory/).,
Vulnerabilities,mskb,string,Corresponds to a Microsoft Knowledge Base article number (http://support.microsoft.com/kb/).,
Vulnerabilities,severity,string,"The severity of the vulnerability detection event. Specific values are required. Use vendor_severity for the vendor's own human readable strings (such as Good, Bad, and Really Bad).Note: This field is a string. Use severity_id for numeric data types.","recommended
required for pytest-splunk-addon
prescribed values:critical, high,  medium, informational, low"
Vulnerabilities,severity_id,string,The numeric or vendor specific severity indicator corresponding to the event severity.,
Vulnerabilities,signature,string,"The name of the vulnerability detected on the host, such as HPSBMU02785 SSRT100526 rev.2 - HP LoadRunner Running on Windows, Remote Execution of Arbitrary Code, Denial of Service (DoS).Note: This field has a string value. Use signature_id for numeric indicators.","recommended
required for pytest-splunk-addon"
Vulnerabilities,signature_id,string,The unique identifier or event code of the event signature.,
Vulnerabilities,tag,string,This automatically generated field is used to access tags from within data models. Do not define extractions for this field when writing add-ons.,
Vulnerabilities,url,string,The URL involved in the discovered vulnerability.,
Vulnerabilities,user,string,The user involved in the discovered vulnerability.,
Vulnerabilities,vendor_product,string,The vendor and product that detected the vulnerability. This field can be automatically populated by vendor and product fields in your data.,recommended
Vulnerabilities,xref,string,"A cross-reference identifier associated with the vulnerability. In most cases, the xref field contains both the short name of the database being cross-referenced and the unique identifier used in the external database.",
Web,action,string,The action taken by the server or proxy.,"recommended
required for pytest-splunk-addon"
Web,app,string,"The application detected or hosted by the server/site such as WordPress, Splunk, or Facebook.",
Web,bytes,number,The total number of bytes transferred (bytes_in + bytes_out).,"recommended
required for pytest-splunk-addon"
Web,bytes_in,number,The number of inbound bytes transferred.,"recommended
required for pytest-splunk-addon"
Web,bytes_out,number,The number of outbound bytes transferred.,"recommended
required for pytest-splunk-addon"
Web,cached,boolean,Indicates whether the event data is cached or not.,"prescribed values:true, false, 1, 0"
Web,category,string,"The category of traffic, such as may be provided by a proxy server.",required for pytest-splunk-addon
Web,cookie,string,The cookie file recorded in the event.,
Web,dest,string,"The destination of the network traffic (the remote host). You can alias this from more specific fields, such as dest_host, dest_ip, or dest_name.","recommended
required for pytest-splunk-addon"
Web,dest_port,number,The destination port of the web traffic.,required for pytest-splunk-addon
Web,duration,number,"The time taken by the proxy event, in milliseconds.",
Web,http_content_type,string,The content-type of the requested HTTP resource.,recommended
Web,http_method,string,The HTTP method used in the request.,"recommended
prescribed values:GET, PUT,POST, DELETE, HEAD, OPTIONS, CONNECT, TRACE"
Web,http_referrer,string,The HTTP referrer used in the request. The W3C specification and many implementations misspell this as http_referer. Use a FIELDALIAS to handle both key names.,recommended
Web,http_referrer_domain,string,The domain name contained within the HTTP referrer used in the request.,recommended
Web,http_user_agent,string,The user agent used in the request.,"recommended
required for pytest-splunk-addon"
Web,http_user_agent_length,number,The length of the user agent used in the request.,required for pytest-splunk-addon
Web,response_time,number,"The amount of time it took to receive a response, if applicable, in milliseconds.",
Web,site,string,"The virtual site which services the request, if applicable.",
Web,src,string,The source of the network traffic (the client requesting the connection).,"recommended
required for pytest-splunk-addon"
Web,status,string,The HTTP response code indicating the status of the proxy request.,"recommended
required for pytest-splunk-addon
prescribed values:100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 422, 423, 424, 426, 428, 429, 431, 500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511"
Web,tag,string,This automatically generated field is used to access tags from within datamodels. Do not define extractions for this field when writing add-ons.,
Web,uri_path,string,The path of the resource served by the webserver or proxy.,"other:/CertEnroll/Blue%20Coat%20Systems%20Internal.crl
/CertEnroll/PWSVL-NETSVC-01.internal.cacheflow.com_Blue%20Coat%20Systems%20Internal.crt/MFAwTqADAgEAMEcwRTBDMAkGBSsOAwIaBQAEFOoaVMtyzC9gObESY9g1eXf1VM8VBBTl1mBq2WFf4cYqBI6c08kr4S302gIKUCIZdgAAAAAnQA%3D%3D
/bag
/en-US/account/login
/en-US/account/login
/en-US/app/simple_xml_examples/custom_viz_forcedirected
/en-US/config
/en-US/splunkd/__raw/services/apps/local/simple_xml_examples
/en-US/splunkd/__raw/services/configs/conf-web/settings
/en-US/splunkd/__raw/services/data/user-prefs/general
/en-US/splunkd/__raw/services/messages
/en-US/splunkd/__raw/services/messages
/en-US/splunkd/__raw/services/messages
/en-US/splunkd/__raw/services/messages
/en-US/splunkd/__raw/services/saved/searches/_new
/en-US/splunkd/__raw/services/server/info/server-info
/en-US/splunkd/__raw/servicesNS/-/-/search/jobs"
Web,uri_query,string,The path of the resource requested by the client.,"other:?return_to=%2Fen-US%2Fapp%2Fsimple_xml_examples%2Fcustom_viz_forcedirected%3Fearliest%3D0%26latest%3D
?earliest=0&latest=
?autoload=1
?output_mode=json&_=1424960631223
?output_mode=json&_=1424960631232
?output_mode=json&_=1424960631225
?output_mode=json&sort_key=timeCreated_epochSecs&sort_dir=desc&_=1424960631236
?output_mode=json&sort_key=timeCreated_epochSecs&sort_dir=desc&count=1000&_=1424933765618
?output_mode=json&sort_key=timeCreated_epochSecs&sort_dir=desc&count=1000&_=1424933765619
?output_mode=json&sort_key=timeCreated_epochSecs&sort_dir=desc&count=1000&_=1424960631233
?output_mode=json&_=1424960631228
?output_mode=json&_=1424960631224
?id=admin__admin_c2ltcGxlX3htbF9leGFtcGxlcw__search1_1424960633.67&count=1&output_mode=json&_=1424960631243"
Web,url,string,The URL of the requested HTTP resource.,"recommended
required for pytest-splunk-addon
other:http://0.channel36.facebook.com/x/1746719903/
false/p_1243021868=11
http://0.channel36.facebook.com/x/3833188787/
false/p_1243021868=11
http://0.channel37.facebook.com/x/3598566724/
false/p_576766886=1
http://01275269302.channel11.facebook.com/x/
832619022/false/p_792194432=2
http://03978257738.channel38.facebook.com/x/
3905575759/false/p_1576492095=0
http://1.gravatar.com/avatar/72f230f80
db7d667952d596cafbaf928?s=16&d=identicon&r=PG
http://10.0.26.105:8080/secars/secars.dll?h=3397A86
EC64FCE11F15337B7BE75CF1EF7443FFA8
E58454580830E8D41D695469C01E8D128BF891F4D
0438A70BE3E0A0D7BABD610DE3A588DF1804F823
CD509F0A2177AD97F7B9F3D09BEDA005C241B873
349D525C0264A9F1655FD408F70DD465574D5E8E
BE0DC29030A6365C1F025CB2954E2C38E0404CE4
D24970B2613EB394E2611FD7EC8EB2AD84318421CD
40DF01E6DF002AFF775653030012EF432D59072C0
5F1A939A6C1467CC3A129801587BE559CB16653513
3EAA6C78D3C4BDEC6D795C2934A176DACBB3839
8ED490322037DDB59101EE725138FF8534D89657F4
43F084ACE66DF159581AEF495F317536C34477D005
49B514A81CC689BFB7ACA7C10399C2C7BD76319876
C9890FB4172BBC7CBDF50F7CE0B164BE7F8D8228E9
555E39EE9D0F50B6CE3F610533544A959087F03FCD
16D8FDF0F9C5EB692E3C7EE61B75272961CC29A05D
5F3A1629BBF7C70044BBC65D30812B8EB3E0C7510C
DA0F636808B32925481602F702714C60ADC7040F58
CACA4BDD61D776C796D5344495B93AC08F16FC851E
3FB157CEBB563CC1
http://10.10.8.60/
http://10.120.109.82/en-US/static/@255606:0/app/simple_
xml_examples/components/forcedirected/
forcedirected.js?_=1424960631242
http://10.120.251.250/en-US/account/login"
Web,url_domain,string,The domain name contained within the URL of the requested HTTP resource.,recommended
Web,url_length,number,The length of the URL.,
Web,user,string,The user that requested the HTTP resource.,recommended
Web,vendor_product,string,"The vendor and product of the proxy server, such as Squid Proxy Server. This field can be automatically populated by vendor and product fields in your data.",recommended
Storage,error_code,string,The error code that occurred while accessing the storage account.,other: NoSuchBucket
Storage,operation,string,The operation performed on the storage account.,other: REST.PUT.OBJECT
Storage,storage_name,string,The name of the bucket or storage account.,other: es-csm-files
ENDMSG
```
---
### rag/splunk_sourcetypes.csv
```bash
cat > "/opt/SmartSOC/web/rag/splunk_sourcetypes.csv" <<"ENDMSG"
Package,Sourcetype,Documentation_URL
Splunk_SA_CIM,stash_common_action_model,http://docs.splunk.com/Documentation/CIM/
Splunk_SA_CIM,audittrail,http://docs.splunk.com/Documentation/CIM/
Splunk_SA_CIM,splunkd,http://docs.splunk.com/Documentation/CIM/
Splunk_SA_CIM,splunk_web_access,http://docs.splunk.com/Documentation/CIM/
Splunk_TA_apache,apache:access:json,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_apache,apache:access:kv,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_apache,apache:access:combined,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_apache,apache:access,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_apache,apache:error,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_linux,ari:ta:asset,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_linux,ari:ta:software,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_mac,ari:ta:asset,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_mac,ari:ta:software,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_win,ari:ta:asset,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_ari_win,ari:ta:software,https://docs.splunk.com/Documentation/AddOns/latest/ApacheWebServer
Splunk_TA_aws,aws:s3:csv,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudtrail,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatch,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatch:metric,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:billing,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:billing:cur,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:billing:cur:digest,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:config:notification,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:config,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:config:rule,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:description,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:metadata,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatchlogs:guardduty,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatchlogs:vpcflow,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatchlogs:vpcflow:metric,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:inspector,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:inspector:v2:findings,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:s3,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:s3:accesslogs,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudfront:accesslogs,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:elb:accesslogs,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:sqs,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:asl,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,source::aws_cloudwatchevents_securityhub,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:securityhub:finding,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:firehose:json,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:firehose:text,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,source::aws_eventbridgeevents_iam_aa,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:accessanalyzer:finding,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:firehose:cloudwatchevents,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,source::aws_cloudwatchevents_guardduty,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudwatch:guardduty,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:cloudtrail:lake,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws,aws:transitgateway:flowlogs,https://docs.splunk.com/Documentation/AddOns/latest/AWS
Splunk_TA_aws-kinesis-firehose,aws:firehose:json,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:firehose:text,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:firehose:cloudwatchevents,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:cloudwatchlogs:vpcflow,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,source::aws_firehose_cloudtrail,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:cloudtrail,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,source::aws_cloudwatchevents_guardduty,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:cloudwatch:guardduty,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,source::aws_cloudwatchevents_securityhub,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:securityhub:finding,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:metadata,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,source::aws_eventbridgeevents_iam_aa,https://github.com/splunk/cloudfwd.
Splunk_TA_aws-kinesis-firehose,aws:accessanalyzer:finding,https://github.com/splunk/cloudfwd.
Splunk_TA_bit9-carbonblack,bit9:carbonblack:json,http://docs.splunk.com/Documentation/AddOns/latest/Bit9CarbonBlack
Splunk_TA_bluecoat-proxysg,bluecoat,https://docs.splunk.com/Documentation/AddOns/latest/BlueCoatProxySG
Splunk_TA_bluecoat-proxysg,bluecoat:proxysg:access:syslog,https://docs.splunk.com/Documentation/AddOns/latest/BlueCoatProxySG
Splunk_TA_bluecoat-proxysg,bluecoat:proxysg:access:file,https://docs.splunk.com/Documentation/AddOns/latest/BlueCoatProxySG
Splunk_TA_bluecoat-proxysg,bluecoat:proxysg:access:kv,https://docs.splunk.com/Documentation/AddOns/latest/BlueCoatProxySG
Splunk_TA_box,box:events,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:users,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:groups,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:folder,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:folderCollaboration,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:fileComment,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:file,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:fileTask,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:filecontent,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:filecontent:csv,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:filecontent:xml,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_box,box:filecontent:json,http://docs.splunk.com/Documentation/AddOns/latest/Box
Splunk_TA_checkpoint_log_exporter,cp_log,
Splunk_TA_checkpoint_log_exporter,cp_log:syslog,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:audit,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:ids,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:web,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:firewall,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:sessions,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:email,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:endpoint,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:ids_malware,
Splunk_TA_checkpoint_log_exporter,source::checkpoint:network,
Splunk_TA_cisco-asa,source::tcp:514,http://docs.splunk.com/Documentation/AddOns/latest/CiscoASA
Splunk_TA_cisco-asa,source::udp:514,http://docs.splunk.com/Documentation/AddOns/latest/CiscoASA
Splunk_TA_cisco-asa,syslog,http://docs.splunk.com/Documentation/AddOns/latest/CiscoASA
Splunk_TA_cisco-asa,cisco_asa,http://docs.splunk.com/Documentation/AddOns/latest/CiscoASA
Splunk_TA_cisco-asa,cisco:asa,http://docs.splunk.com/Documentation/AddOns/latest/CiscoASA
Splunk_TA_cisco-esa,cisco:esa:authentication,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:antispam,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:error_logs,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:content_scanner,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:system_logs,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:textmail,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:amp,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:http,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco_esa,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:legacy,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:cef,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:bounce,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-esa,cisco:esa:delivery,http://docs.splunk.com/Documentation/AddOns/latest/CiscoESA
Splunk_TA_cisco-ise,cisco:ise,https://docs.splunk.com/Documentation/AddOns/latest/CiscoISE
Splunk_TA_cisco-ise,cisco:ise:syslog,https://docs.splunk.com/Documentation/AddOns/latest/CiscoISE
Splunk_TA_cisco-ise,syslog,https://docs.splunk.com/Documentation/AddOns/latest/CiscoISE
Splunk_TA_cisco-ise,Cisco:ISE:Syslog,https://docs.splunk.com/Documentation/AddOns/latest/CiscoISE
Splunk_TA_cisco-ucs,source::cisco:ucs:faultInst,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:topSystem,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:firmwareRunning,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:storageLocalDisk,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:fabricVsan,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:fabricVlan,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:fabricDceSwSrvEp,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:computeRackUnit,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:computeBlade,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentPsu,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentChassis,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentSwitchCard,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:vnicEtherIf,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:lsServer,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:fabricEthLanPcEp,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:fabricEthLanPc,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherPIo,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentIOCard,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:swSystemStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherTxStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherPauseStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherRxStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherLossStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:etherErrStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:adaptorVnicStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:processorEnvStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:computeMbTempStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:computeMbPowerStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentChassisStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-ucs,source::cisco:ucs:equipmentPsuStats,http://docs.splunk.com/Documentation/AddOns/latest/CiscoUCS
Splunk_TA_cisco-wsa,cisco:wsa:l4tm,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_cisco-wsa,cisco:wsa:squid:new,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_cisco-wsa,cisco:wsa:squid,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_cisco-wsa,cisco:wsa:w3c,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_cisco-wsa,cisco:wsa:w3c:recommended,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_cisco-wsa,cisco:wsa:syslog,http://docs.splunk.com/Documentation/AddOns/latest/CiscoWSA
Splunk_TA_citrix-netscaler,citrix:netscaler:nitro,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,citrix:netscaler:syslog,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,citrix:netscaler:ipfix,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,citrix:netscaler:ipfix:syslog,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,citrix:netscaler:appfw,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,citrix:netscaler:appfw:cef,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:system,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:systemmemory,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::config:nsversion,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::config:Interface,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::config:nshardware,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:ns,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:protocolhttp,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:protocolip,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:ssl,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:hanode,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:service,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::stat:servicegroup,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::config:service,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_citrix-netscaler,source::config:servicegroup,https://docs.splunk.com/Documentation/AddOns/latest/CitrixNetScaler
Splunk_TA_CrowdStrike_FDR,crowdstrike:events:external,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:events:ztha,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:inventory:aidmaster,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:inventory:managedassets,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:inventory:notmanaged,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:inventory:appinfo,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:inventory:userinfo,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:events:sensor,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_CrowdStrike_FDR,crowdstrike:events:sensor:ithr,http://docs.splunk.com/Documentation/AddOns/latest/CrowdStrikeFDR
Splunk_TA_cyberark,cyberark:epv:cef,http://docs.splunk.com/Documentation/AddOns/latest/CyberArk/About
Splunk_TA_cyberark,cyberark:pta:cef,http://docs.splunk.com/Documentation/AddOns/latest/CyberArk/About
Splunk_TA_cyberark_epm,cyberark:epm:application:events,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:policy:audit,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:threat:detection,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:aggregated:events,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:raw:events,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:raw:policy:audit,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:aggregated:policy:audit,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:policies,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:computers,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:computer:groups,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:admin:audit,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_cyberark_epm,cyberark:epm:account:admin:audit,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_esxilogs,vmw-syslog,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_esxilogs,vmware:esxlog:vmkernel,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_esxilogs,vmware:esxlog:vmkwarning,http://docs.splunk.com/Documentation/AddOns/latest/CyberArkEPM
Splunk_TA_f5-bigip,f5_bigip:irule:dns:request,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:irule:dns:response,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:globallb,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:irule:http,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:irule:lb:failed,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:locallb,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:locallb:pool,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:syslog,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:system:systeminfo,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:system:statistics,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:system:disk,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:management:device,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:networking:interfaces,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:networking:adminip,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:management:usermanagement,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:networking,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5_bigip:icontrol:management,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:failed::irule,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:gtm:dns:request:irule,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:gtm:dns:response:irule,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:gtm:globallb:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:http:irule,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:failed:irule,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:locallb:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:locallb:pool:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:syslog,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:secure,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:ssl:error,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:tcl:error,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:traffic,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ltm:log:error,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:system:systeminfo:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:system:statistics:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:system:disk:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:management:device:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:networking:interfaces:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:networking:adminip:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:management:usermanagement:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:networking:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:management:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:asm:syslog,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:apm:syslog,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:telemetry:json,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,source::f5:bigip:avr,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,source::f5:bigip:syslog,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,source::f5:bigip:asm,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,source::f5:bigip:afm,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:networking:interfaces:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:networking:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:networking:adminip:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:system:disk:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:system:statistics:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:management:device:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:management:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:management:usermanagement:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:gtm:globallb:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:gtm:globallb:pool:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:system:systeminfo:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:ltm:locallb:pool:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_f5-bigip,f5:bigip:ts:ltm:locallb:icontrol,https://docs.splunk.com/Documentation/AddOns/latest/F5BIGIP
Splunk_TA_github,github:enterprise:audit,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_github,github:cloud:audit,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_github,github:cloud:user,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_github,github:cloud:code:scanning:alerts,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_github,github:cloud:dependabot:scanning:alerts,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_github,github:cloud:secret:scanning:alerts,https://docs.splunk.com/Documentation/AddOns/released/GitHub/About
Splunk_TA_google-cloudplatform,google:billing:json,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:billing:csv,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:billing:report,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:pubsublite:message,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:pubsub:message,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:pubsub:audit:admin_activity,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:pubsub:audit:system_event,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:pubsub:audit:data_access,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gsuite:pubsub:audit:auth,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:gsuite:admin:directory:users,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:buckets:xmldata,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:buckets:jsondata,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:compute:instance,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:compute:vpc_flows,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:buckets:accesslogs,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_google-cloudplatform,google:gcp:security:alerts,http://docs.splunk.com/Documentation/AddOns/latest/GoogleCloud
Splunk_TA_Google_Workspace,gws:reports:token,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:admin,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:login,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:drive,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:chrome,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:mobile,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:chat,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:data_studio,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:saml,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:groups_enterprise,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:gcp,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:calendar,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:context_aware_access,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:rules,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:gmail,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:alerts,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:users:identity,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:usage_reports:customer,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:usage_reports:user,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:usage_reports:entity,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_Google_Workspace,gws:reports:access_transparency,https://github.com/googleapis/google-auth-library-python/blob/master/LICENSE
Splunk_TA_haproxy,haproxy:http,http://docs.splunk.com/Documentation/AddOns/latest/HAProxy
Splunk_TA_haproxy,haproxy:tcp,http://docs.splunk.com/Documentation/AddOns/latest/HAProxy
Splunk_TA_haproxy,haproxy:clf:http,http://docs.splunk.com/Documentation/AddOns/latest/HAProxy
Splunk_TA_haproxy,haproxy:splunk:http,http://docs.splunk.com/Documentation/AddOns/latest/HAProxy
Splunk_TA_ibm-was,ibm:was:hpel,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:ivtClientLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:wsadminTraceout,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:nativeStdOutLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:nativeStdErrLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:startServerLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:stopServerLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:serverStatus,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:systemOutLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:systemErrLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:javacore,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:httpLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:httpErrorLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:ffdc,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:profileManagementLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:profileCreationLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:textLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:serverExceptionLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:activityLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:manageprofiles,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:derby,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:orbtrc,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:addNodeLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:jmx,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:serverIndex,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_ibm-was,ibm:was:gcLog,https://docs.splunk.com/Documentation/AddOns/latest/IBMWAS
Splunk_TA_imperva-waf,imperva:waf,http://docs.splunk.com/Documentation/AddOns/latest/ImpervaWAF
Splunk_TA_imperva-waf,imperva:waf:security:cef,http://docs.splunk.com/Documentation/AddOns/latest/ImpervaWAF
Splunk_TA_imperva-waf,imperva:waf:system:cef,http://docs.splunk.com/Documentation/AddOns/latest/ImpervaWAF
Splunk_TA_imperva-waf,imperva:waf:firewall:cef,http://docs.splunk.com/Documentation/AddOns/latest/ImpervaWAF
Splunk_TA_imperva-waf,imperva_waf,http://docs.splunk.com/Documentation/AddOns/latest/ImpervaWAF
Splunk_TA_infoblox,infoblox:port,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_infoblox,infoblox:file,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_infoblox,infoblox:dhcp,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_infoblox,infoblox:dns,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_infoblox,infoblox:threatprotect,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_infoblox,infoblox:audit,https://docs.splunk.com/Documentation/AddOns/released/Infoblox/About
Splunk_TA_isc-bind,isc:bind:query,http://docs.splunk.com/Documentation/AddOns/latest/ISCBIND
Splunk_TA_isc-bind,isc:bind:queryerror,http://docs.splunk.com/Documentation/AddOns/latest/ISCBIND
Splunk_TA_isc-bind,isc:bind:lameserver,http://docs.splunk.com/Documentation/AddOns/latest/ISCBIND
Splunk_TA_isc-bind,isc:bind:network,http://docs.splunk.com/Documentation/AddOns/latest/ISCBIND
Splunk_TA_isc-bind,isc:bind:transfer,http://docs.splunk.com/Documentation/AddOns/latest/ISCBIND
Splunk_TA_isc-dhcp,isc:dhcp,http://docs.splunk.com/Documentation/AddOns/latest/ISCDHCP
Splunk_TA_Jira_Cloud,jira:cloud:audit:log,
Splunk_TA_Jira_Cloud,jira:cloud:issues,
Splunk_TA_Jira_Data_Center,jira:datacenter:audit:log,
Splunk_TA_Jira_Data_Center,jira:datacenter:security:log,
Splunk_TA_Jira_Data_Center,jira:datacenter:log,
Splunk_TA_jmx,jmx,https://docs.splunk.com/Documentation/AddOns/latest/JMX
Splunk_TA_juniper,juniper,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,netscreen:firewall,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:idp,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:idp:structured,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:firewall,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:firewall:structured,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:aamw:structured,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:secintel:structured,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_juniper,juniper:junos:snmp,https://docs.splunk.com/Documentation/AddOns/latest/Juniper
Splunk_TA_kafka,kafka:controllerLog,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_kafka,kafka:serverLog,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_kafka,kafka:stateChangeLog,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_kafka,kafka:logStats,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_kafka,kafka:serverStats,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_kafka,kafka:networkStats,http://docs.splunk.com/Documentation/AddOns/latest/Kafka
Splunk_TA_linux,linux:collectd:graphite,https://docs.splunk.com/Documentation/AddOns/latest/Linux
Splunk_TA_linux,linux:collectd:http:json,https://docs.splunk.com/Documentation/AddOns/latest/Linux
Splunk_TA_linux,linux:collectd:http:metrics,https://docs.splunk.com/Documentation/AddOns/latest/Linux
Splunk_TA_linux,linux:audit,https://docs.splunk.com/Documentation/AddOns/latest/Linux
Splunk_TA_mcafee-wg,mcafee:wg:kv,http://docs.splunk.com/Documentation/AddOns/latest/McAfeeWG
Splunk_TA_mcafee_epo_syslog,mcafee:epo:syslog,https://docs.splunk.com/Documentation/AddOns/McAfeeEPOSyslog/About
Splunk_TA_mcafee_nsp,mcafee:nsp,
Splunk_TA_mcafee_nsp,source::mcafee:nsp:alert,
Splunk_TA_mcafee_nsp,source::mcafee:nsp:firewall,
Splunk_TA_mcafee_nsp,source::mcafee:nsp:audit,
Splunk_TA_mcafee_nsp,source::mcafee:nsp:fault,
Splunk_TA_microsoft-cloudservices,ms:o365:management,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:virtualMachine,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:networkInterfaceCard,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:publicIPAddress,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:virtualNetwork,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:azure:audit,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:storage:table,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:vm:metrics,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:kql,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:kql:stats,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,ms:0365:jobinsight:input,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:storage:blob:json,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:storage:blob:xml,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:azure:eventhub,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,azure:monitor:aad,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:azure:security:alert,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:azure:security:recommendation,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,azure:monitor:activity,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,azure:monitor:resource,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:consumption:reservation:recommendation,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:consumption:billing,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:metrics,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:metrics:events,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:securityGroup,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:disk,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:image,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:snapshot,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:resourceGroup,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:subscriptions,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:topology,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-cloudservices,mscs:resource:resourceGraph,http://docs.splunk.com/Documentation/AddOns/latest/MSCloudServices
Splunk_TA_microsoft-hyperv,microsoft:hyperv:vm,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:vm:ext,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:host,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:host:ext,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:vm:disk,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:vm:network,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:host:switch,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:perf:host,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:perf:vm,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,microsoft:hyperv:perf:datastore,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-Compute-Admin,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-Hypervisor-Operational,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-SynthNic-Admin,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-VmSwitch-Operational,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Networking,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Operational,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-hyperv,source::WinEventLog:Microsoft-Windows-Hyper-V-Worker-Admin,https://docs.splunk.com/Documentation/AddOns/latest/MSHyperV
Splunk_TA_microsoft-iis,ms:iis:auto,https://docs.splunk.com/Documentation/AddOns/latest/MSIIS
Splunk_TA_microsoft-iis,ms:iis:splunk,https://docs.splunk.com/Documentation/AddOns/latest/MSIIS
Splunk_TA_microsoft-scom,microsoft:scom:alert,https://docs.splunk.com/Documentation/AddOns/latest/MSSCOM
Splunk_TA_microsoft-scom,microsoft:scom:performance,https://docs.splunk.com/Documentation/AddOns/latest/MSSCOM
Splunk_TA_microsoft-sqlserver,mssql:errorlog,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:agentlog,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:instance,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:os:dm_os_performance_counters,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:table,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:user,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:os:dm_os_sys_info,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:instancestats,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:execution:dm_exec_sessions,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:transaction:dm_tran_locks,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:execution:dm_exec_query_stats,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:trclog,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:databases,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:execution:dm_exec_connections,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,mssql:audit,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:memory,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:network,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:processor,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:buffer_manager,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:databases,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:logicaldisk,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:physicaldisk,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:paging_file,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:process,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserverhost:system,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:memory_manager,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:general_statistics,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:sql_statistics,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:access_methods,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:latches,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:sql_errors,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:locks,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft-sqlserver,Perfmon:sqlserver:transactions,http://docs.splunk.com/Documentation/AddOns/latest/MSSQLServer
Splunk_TA_microsoft_sysmon,source::XmlWinEventLog:Microsoft-Windows-Sysmon/Operational,https://docs.splunk.com/Documentation/AddOns/latest/MSSysmon
Splunk_TA_microsoft_sysmon,XmlWinEventLog:Microsoft-Windows-Sysmon/Operational,https://docs.splunk.com/Documentation/AddOns/latest/MSSysmon
Splunk_TA_microsoft_sysmon,XmlWinEventLog:WEC-Sysmon,https://docs.splunk.com/Documentation/AddOns/latest/MSSysmon
Splunk_TA_microsoft_sysmon,host::WinEventLogForwardHost,https://docs.splunk.com/Documentation/AddOns/latest/MSSysmon
Splunk_TA_mysql,mysql:slowQueryLog,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:slowQueryLogDb,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:generalQueryLog,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:generalQueryLogDb,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:errorLog,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:database,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:databaseProcess,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:processInfo,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:status,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:user,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:variables,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:tableStatus,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:instance:stats,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:transaction:stats,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:connection:stats,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:innodbStatus,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:innodbLockWaits,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_mysql,mysql:audit,http://docs.splunk.com/Documentation/AddOns/latest/MySQL
Splunk_TA_nagios-core,nagios:servicestatus,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:notifications,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:commenthistory,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:comments,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:customvariablestatus,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:downtimehistory,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:eventhandlers,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:hostchecks,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:hoststatus,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:processevents,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:programstatus,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:scheduleddowntime,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:servicechecks,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:systemcommands,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:core:hostperf,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:core:serviceperf,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nagios-core,nagios:core,http://docs.splunk.com/Documentation/AddOns/latest/NagiosCore
Splunk_TA_nginx,nginx:plus:kv,https://docs.splunk.com/Documentation/AddOns/latest/Nginx
Splunk_TA_nginx,nginx:plus:api,https://docs.splunk.com/Documentation/AddOns/latest/Nginx
Splunk_TA_nginx,nginx:plus:access,https://docs.splunk.com/Documentation/AddOns/latest/Nginx
Splunk_TA_nginx,nginx:plus:error,https://docs.splunk.com/Documentation/AddOns/latest/Nginx
Splunk_TA_nginx,nginx:app:protect,https://docs.splunk.com/Documentation/AddOns/latest/Nginx
Splunk_TA_nix,config_file,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,dhcpd,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,vmstat_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,cpu_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,df_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,interfaces_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,iostat_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,ps_metric,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,cpu,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,df,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,hardware,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,interfaces,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,iostat,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,nfsiostat,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,lastlog,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,lsof,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,netstat,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,bandwidth,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,openPorts,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,Unix:ListeningPorts,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,package,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,protocol,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,ps,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,time,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,top,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,usersWithLoginPrivs,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,who,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,vmstat,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,Unix:UserAccounts,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,Linux:SELinuxConfig,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,linux_audit,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,Unix:Service,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,aix_secure,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,osx_secure,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,linux_secure,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,syslog,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,bash_history,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
Splunk_TA_nix,auditd,https://docs.splunk.com/Documentation/AddOns/released/UnixLinux/
splunk_ta_o365,o365:management:activity,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:service:status,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:service:message,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:graph:api,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:cas:api,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:service:healthIssue,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:service:updateMessage,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:reporting:messagetrace,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
splunk_ta_o365,o365:metadata,http://docs.splunk.com/Documentation/AddOns/latest/MSO365
Splunk_TA_okta_identity_cloud,OktaIM2:group,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_okta_identity_cloud,OktaIM2:app,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_okta_identity_cloud,OktaIM2:user,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_okta_identity_cloud,OktaIM2:log,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_okta_identity_cloud,OktaIM2:groupUser,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_okta_identity_cloud,OktaIM2:appUser,https://docs.splunk.com/Documentation/AddOns/released/OktaIDC/About
Splunk_TA_oracle,oracle:audit:text,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:audit:xml,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:alert:text,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:alert:xml,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:listener:text,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:listener:xml,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:trace,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:incident,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:database,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:instance,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:sga,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:tablespaceMetrics,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:session,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:sysPerf,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:osPerf,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:audit:unified,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:libraryCachePerf,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:dbFileIoPerf,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:connections,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:pool:connections,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:database:size,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:table,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:user,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:query,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:sqlMonitor,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_oracle,oracle:connections:poolStats,https://docs.splunk.com/Documentation/AddOns/latest/Oracle
Splunk_TA_ossec,ossec,http://docs.splunk.com/Documentation/AddOns/latest/OSSEC
Splunk_TA_paloalto_networks,pan_log,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:log,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:firewall,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:firewall_cloud,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_threat,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:threat,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_traffic,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:traffic,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_system,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:system,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_globalprotect,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:globalprotect,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_decryption,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:decryption,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan_config,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:config,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:correlation,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:iot_alert,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:iot_vulnerability,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:iot_device,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:data:security,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_paloalto_networks,pan:xdr_incident,https://pypi.org/project/charset-normalizer/3.1.0/
Splunk_TA_Phantom,phantom:daemon,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,phantom:supervisord,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,postgres,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,phantom:daemon:ingestd,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,phantom:logs,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,nginx:plus:error,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_Phantom,phantom:supervisord,https://docs.splunk.com/Documentation/ITSICP/current/Config/AboutPhantom
Splunk_TA_remedy,remedy:incident,http://docs.splunk.com/Documentation/AddOns/latest/Remedy
Splunk_TA_remedy,remedy:incident:worklog,http://docs.splunk.com/Documentation/AddOns/latest/Remedy
Splunk_TA_remedy,remedy:audit,http://docs.splunk.com/Documentation/AddOns/latest/Remedy
Splunk_TA_rsa-dlp,rsa:dlp,http://docs.splunk.com/Documentation/AddOns/latest/RSADLP
Splunk_TA_rsa-securid,rsa:securid:syslog,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurID
Splunk_TA_rsa-securid,rsa:securid:system:syslog,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurID
Splunk_TA_rsa-securid,rsa:securid:admin:syslog,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurID
Splunk_TA_rsa-securid,rsa:securid:runtime:syslog,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurID
Splunk_TA_rsa_securid_cas,rsa:securid:cas:adminlog:json,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurIDCAS
Splunk_TA_rsa_securid_cas,rsa:securid:cas:usereventlog:json,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurIDCAS
Splunk_TA_rsa_securid_cas,rsa:securid:cas:riskuser:json,https://docs.splunk.com/Documentation/AddOns/latest/RSASecurIDCAS
Splunk_TA_SAA,splunk:aa:job,
Splunk_TA_SAA,splunk:aa:job:task,
Splunk_TA_SAA,splunk:aa:job:resource,
Splunk_TA_SAA,splunk:aa:forensic:detections,
Splunk_TA_SAA,splunk:aa:forensic:dnsrequests,
Splunk_TA_SAA,splunk:aa:forensic:files,
Splunk_TA_SAA,splunk:aa:forensic:hosts,
Splunk_TA_SAA,splunk:aa:forensic:http,
Splunk_TA_SAA,splunk:aa:forensic:mitreattacks,
Splunk_TA_SAA,splunk:aa:forensic:network,
Splunk_TA_SAA,splunk:aa:forensic:processes,
Splunk_TA_SAA,splunk:aa:forensic:registrykeys,
Splunk_TA_SAA,splunk:aa:forensic:strings,
Splunk_TA_SAA,splunk:aa:forensic:tls,
Splunk_TA_SAA,splunk:aa:forensic:urls,
Splunk_TA_SAA,splunk:aa:forensic:screenshots,
Splunk_TA_SAA,splunk:aa:forensic:savedartifacts,
Splunk_TA_SAA,splunk:aa:forensic:images,
Splunk_TA_salesforce,sfdc:logfile,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:dashboard,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:user,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:account,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:object,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:opportunity,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:loginhistory,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:report,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_salesforce,sfdc:contentversion,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
splunk_ta_sim,splunk_ta_sim,https://docs.splunk.com/Documentation/AddOns/latest/Salesforce
Splunk_TA_snow,snow:incident,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:change_request,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:change_task,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:problem,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sysevent,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:em_event,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_user_group,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_user,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmn_location,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_choice,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_list,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmn_location_list,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_rel_ci,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_service,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_server,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_vm,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_infra_service,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_db_instance,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:cmdb_ci_app_server,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_user_list,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_user_group_list,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_snow,snow:sys_choice_list,https://docs.splunk.com/Documentation/AddOns/latest/ServiceNow
Splunk_TA_sophos,source::WinEventLog:Application,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,WinEventLog:Application:sophos,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,source::WinEventLog:Sophos Patch,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,WinEventLog:SophosPatch,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:threats,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:webdata,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:firewall,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:appcontrol,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:devicecontrol,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:tamperprotection,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:datacontrol,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:computerdata,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:sec,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:utm:firewall,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:utm:ips,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_sophos,sophos:swa,https://docs.splunk.com/Documentation/AddOns/released/Sophos/Description
Splunk_TA_squid,squid:access,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_squid,squid:access:recommended,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:log,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:stats,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:dhcp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:http,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:smtp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:pop3,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:imap,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:tcp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:tns,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:postgres,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:mysql,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:tds,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:dns,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:udp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:xmpp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:snmp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:ftp,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_stream_wire_data,stream:netflow,http://docs.splunk.com/Documentation/AddOns/latest/Squid
Splunk_TA_symantec-dlp,symantec:dlp:syslog,http://docs.splunk.com/Documentation/AddOns/latest/SymantecDLP
Splunk_TA_symantec-ep,symantec:ep:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:agt_system:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:agt:system:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:scm_system:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:scm:system:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:agent:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:agent:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:behavior:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:behavior:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:risk:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:risk:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:security:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:security:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:scan:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:scan:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:proactive:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:proactive:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:admin:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:admin:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:policy:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:policy:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:packet:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:packet:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:traffic:file,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_symantec-ep,symantec:ep:traffic:syslog,https://docs.splunk.com/Documentation/AddOns/latest/SymantecEP
Splunk_TA_sysmon-for-linux,sysmon:linux,
Splunk_TA_tomcat,tomcat:jmx,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_tomcat,tomcat:runtime:log,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_tomcat,tomcat:access:log,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_tomcat,tomcat:access:log:splunk,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vclog,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:vpxd,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:vws,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:stats,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:cim-diag,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:sms,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:vpxd-profiler,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:vpxd-alert,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vcenter,vmware:vclog:vim-tomcat-shared,https://docs.splunk.com/Documentation/AddOns/latest/Tomcat
Splunk_TA_vmware,vmware:perf:cpu,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:disk,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:mem,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:clusterServices,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:datastore,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:hbr,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:managementAgent,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:net,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:rescpu,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:power,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:storageAdapter,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:storagePath,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:sys,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:vcDebugInfo,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:vcResources,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:virtualDisk,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:vmop,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:perf:vflashModule,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:events,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:tasks,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:clustercomputeresource,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:datastore,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:hierarchy,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:hostsystem,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:resourcepool,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware,vmware:inv:vm,https://splunkbase.splunk.com/app/3215/.
Splunk_TA_vmware_inframon,vmware_inframon:events,
Splunk_TA_vmware_inframon,vmware_inframon:tasks,
Splunk_TA_vmware_inframon,vmware_inframon:inv:clustercomputeresource,
Splunk_TA_vmware_inframon,vmware_inframon:inv:datastore,
Splunk_TA_vmware_inframon,vmware_inframon:inv:hostsystem,
Splunk_TA_vmware_inframon,vmware_inframon:inv:vm,
Splunk_TA_websense-cg,websense:cg:kv,http://docs.splunk.com/Documentation/AddOns/latest/WebsenseCG
Splunk_TA_websense-cg,websense,http://docs.splunk.com/Documentation/AddOns/latest/WebsenseCG
Splunk_TA_websense-dlp,websense:dlp:system:cef,http://docs.splunk.com/Documentation/AddOns/latest/WebsenseDLP
Splunk_TA_windows,ActiveDirectory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,DhcpSrvLog,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,host::WinEventLogForwardHost,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::XmlWinEventLog:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::XmlWinEventLog:Security,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::XmlWinEventLog:Application,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::XmlWinEventLog:Microsoft-Windows-PowerShell/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:Microsoft-Windows-PowerShell/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:Application,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:Security,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:System:IAS,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,source::WinEventLog:ForwardedEvents,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WindowsUpdateLog,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinRegistry,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,wmi,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:ComputerSystem,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:Processor,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:Processor,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:Network_Interface,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:Network_Interface,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:DFS_Replicated_Folders,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:NTDS,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:DNS,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:CPU,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:CPU,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:ProcessorInformation,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:ProcessorInformation,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:CPUTime,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:LogicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:LogicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:PhysicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:PhysicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:FreeDiskSpace,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:LogicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:LocalPhysicalDisk,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:LocalNetwork,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:Process,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:Process,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Script:InstalledApps,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:InstalledUpdates,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Script:ListeningPorts,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:LocalProcesses,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:Memory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:Memory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:Network,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,PerfmonMk:Network,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:Memory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:Service,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Script:TimesyncConfiguration,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Script:TimesyncStatus,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:Uptime,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:UserAccounts,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:Version,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:ScheduledJobs,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinHostMon,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:WinEventLog:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:WinEventLog:Security,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WMI:WinEventLog:Application,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:FreeDiskSpace,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:CPUTime,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Perfmon:LocalNetwork,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Security,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Application,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:System:IAS,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-AppLocker/MSI and Script,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-AppLocker/Packaged app-Deployment,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-AppLocker/Packaged app-Execution,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-DNS-Client/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-DriverFrameworks-UserMode/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Setup,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-Application-Experience/Program-Inventory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-CAPI2/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-CodeIntegrity/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-Defender/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-LSA/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-NetworkProfile/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-WLAN-Autoconfig/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-Kernel-PnP/Device Configuration,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-PowerShell/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Windows PowerShell,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-PrintService/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-WinRM/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-SmartCard-Audit/Authentication,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-SMBClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TaskScheduler/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Admin,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TerminalServices-RemoteConnectionManager/Admin,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-TerminalServices-RDPClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Microsoft-Windows-Windows Defender/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Security,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Application,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:System,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-AppLocker/EXE and DLL,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-AppLocker/MSI and Script,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-AppLocker/Packaged app-Deployment,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-AppLocker/Packaged app-Execution,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-WindowsUpdateClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-DNS-Client/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-DriverFrameworks-UserMode/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Setup,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-Application-Experience/Program-Inventory,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-CAPI2/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-CodeIntegrity/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-Defender/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-LSA/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-NetworkProfile/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-WLAN-Autoconfig/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-Kernel-PnP/Device Configuration,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-PowerShell/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Windows PowerShell,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-PrintService/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-WinRM/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-SmartCard-Audit/Authentication,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-SMBClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TaskScheduler/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Admin,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TerminalServices-RemoteConnectionManager/Admin,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-TerminalServices-RDPClient/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,XmlWinEventLog:Microsoft-Windows-Windows Defender/Operational,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:DFS-Replication,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Directory-Service,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:File-Replication-Service,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:Key-Management-Service,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,WinEventLog:DNS-Server,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,Script:NetworkConfiguration,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:Health,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:SiteInfo,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:Replication,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:Netlogon,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:SubnetAffinity,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:DNS-Zone-Information,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:DNS-Health,http://docs.splunk.com/Documentation/WindowsAddOn/latest
Splunk_TA_windows,MSAD:NT6:DNS,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-ClientAccess,MSExchange:2007:RPCClientAccess,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-ClientAccess,MSExchange:2010:RPCClientAccess,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-ClientAccess,MSExchange:2013:RPCClientAccess,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-ClientAccess,source::Powershell,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-Mailbox,MSExchange:2013:MessageTracking,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-Exchange-Mailbox,source::Powershell,http://docs.splunk.com/Documentation/WindowsAddOn/latest
TA-ONTAP-FieldExtractions,ontap:perf,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::SystemPerfHandler,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::AggrPerfHandler,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::VolumePerfHandler,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::LunPerfHandler,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::DiskPerfHandler,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,ontap:volume,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,ontap:aggr,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,ontap:disk,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,ontap:system,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,source::system-get-info,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-ONTAP-FieldExtractions,ontap:lun,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-SMTP-Reputation,MSExchange:Reputation,https://docs.splunk.com/Documentation/AddOns/released/NetAppExtractions/About
TA-splunk-add-on-for-victorops,splunk:victorops:users:json,
TA-splunk-add-on-for-victorops,splunk:victorops:teams:json,
TA-splunk-add-on-for-victorops,splunk:victorops:oncall:json,
TA-splunk-add-on-for-victorops,splunk:victorops:incidents:json,
TA-VMW-FieldExtractions,vmware:perf:cpu,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:disk,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:mem,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:clusterServices,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:datastore,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:hbr,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:managementAgent,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:net,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:rescpu,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:power,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:storageAdapter,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:storagePath,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:sys,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:vcDebugInfo,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:vcResources,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:virtualDisk,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:vmop,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:perf:vflashModule,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:events,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:tasks,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:datastore,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:hostsystem,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:vm,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:clustercomputeresource,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:hierarchy,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,vmware:inv:resourcepool,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,source::VMPerf:HostSystem,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-VMW-FieldExtractions,source::VMPerf:VirtualMachine,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-Windows-Exchange-IIS,MSWindows:2013EWS:IIS,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
TA-Windows-Exchange-IIS,MSWindows:2010EWS:IIS,https://docs.splunk.com/Documentation/AddOns/released/VMWExtractions/About
ENDMSG
```
---
### rag/update_repository.py
```bash
cat > "/opt/SmartSOC/web/rag/update_repository.py" <<"ENDMSG"
import requests
import os
import subprocess
from pathlib import Path


def update_elastic_repo():
    """
    Download the list of Elastic packages using GitHub API and maintain local repository.
    """
    # GitHub API URL for packages directory
    api_url = "https://api.github.com/repos/elastic/integrations/contents/packages"
    repo_url = "https://github.com/elastic/integrations.git"
    local_repo_path = "./rag/repos/elastic_repo"
    
    try:
        # Download package list via GitHub API
        print("Downloading Elastic packages list...")
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Handle local repository
        if os.path.exists(local_repo_path):
            print(f"Local repository '{local_repo_path}' exists. Updating...")
            update_local_repository(local_repo_path)
        else:
            print(f"Local repository '{local_repo_path}' doesn't exist. Cloning...")
            clone_repository(repo_url, local_repo_path)
            
    except requests.RequestException as e:
        print(f"Error downloading Elastic packages: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error with git operation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def clone_repository(repo_url, local_path):
    """
    Clone the Elastic integrations repository.
    """
    try:
        # Clone only the packages directory to save space and time
        subprocess.run([
            "git", "clone", "--depth", "1", "--filter=blob:none", repo_url, local_path
        ], check=True)
        
        # Set up sparse checkout for packages directory only
        os.chdir(local_path)
        subprocess.run(["git", "sparse-checkout", "set", "packages"], check=True)
        os.chdir("..")  # Go back to original directory
        
        print(f"Repository cloned successfully to '{local_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")


def update_local_repository(local_path):
    """
    Update the existing local repository.
    """
    try:
        original_dir = os.getcwd()
        os.chdir(local_path)
        
        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin"], check=True)
        
        # Reset to latest main branch
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        
        os.chdir(original_dir)
        print(f"Repository '{local_path}' updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error updating repository: {e}")
        # Go back to original directory even if error occurs
        try:
            os.chdir(original_dir)
        except:
            pass

# update_elastic_repo()ENDMSG
```
---
