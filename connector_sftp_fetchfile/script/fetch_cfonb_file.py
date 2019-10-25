import paramiko

host = 'demo.druidoo.io'
port = 22
username = 'ubuntu'
password = 'druidootest'
remote_path = '/home/ubuntu/CFONB/Files/'
local_path = '/home/goldenom/CFONB/Files/'
file_ext = '.cfo'


def get_client():
    transport = paramiko.Transport((host, port))
    try:
        transport.connect(
            hostkey=None,
            username=username,
            password=password,
            pkey=None,
        )
        return paramiko.SFTPClient.from_transport(transport)
    except Exception as e:
        print(e)


def fetch_files():
    client = get_client()
    if client:
        files = client.listdir(remote_path)
        for file in files:
            if file.endswith(file_ext):
                client.get(remote_path + file, local_path + file)
                print('file %s is fetched successfully!' % file)


fetch_files()