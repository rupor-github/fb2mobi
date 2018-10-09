FROM microsoft/windowsservercore

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

ENV PYTHON_VERSION 3.6.6
ENV PYTHON_RELEASE 3.6.6
ENV PYTHON_PIP_VERSION 18.1
ENV ARCH_INSTALLS='win32 win64'

WORKDIR C:\\Users\\ContainerAdministrator
COPY requirements.txt .
COPY kindlegen.exe .
COPY docker/build.ps1 .

RUN Write-Host 'Starting ...'; \
	$url = ('https://www.python.org/ftp/python/{0}/python-{1}-amd64.exe' -f $env:PYTHON_RELEASE, $env:PYTHON_VERSION); \
	Write-Host ('Downloading {0} ...' -f $url); \
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; \
	Invoke-WebRequest -Uri $url -OutFile 'python64.exe'; \
	\
	Write-Host 'Installing 64 bit ...'; \
	Start-Process python64.exe -Wait \
		-ArgumentList @( \
			'/quiet', \
			'InstallAllUsers=1', \
			'TargetDir=C:\Python64', \
			'PrependPath=0', \
			'Shortcuts=0', \
			'Include_doc=0', \
			'Include_pip=0', \
			'Include_test=0' \
		); \
	\
	Write-Host 'Verifying 64 bit install ...'; \
	Write-Host '  python --version'; C:\Python64\python --version; \
	\
	Remove-Item python64.exe -Force; \
	\
        $url = ('https://www.python.org/ftp/python/{0}/python-{1}.exe' -f $env:PYTHON_RELEASE, $env:PYTHON_VERSION); \
	Write-Host ('Downloading {0} ...' -f $url); \
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; \
	Invoke-WebRequest -Uri $url -OutFile 'python32.exe'; \
	\
	Write-Host 'Installing 32 bit...'; \
	Start-Process python32.exe -Wait \
		-ArgumentList @( \
			'/quiet', \
			'InstallAllUsers=1', \
			'TargetDir=C:\Python32', \
			'PrependPath=0', \
			'Shortcuts=0', \
			'Include_doc=0', \
			'Include_pip=0', \
			'Include_test=0' \
		); \
	\
	Write-Host 'Verifying 32 bit install ...'; \
	Write-Host '  python --version'; C:\Python32\python --version; \
	\
	Remove-Item python32.exe -Force; \
	\
        Write-Host ('Installing pip=={0} ...' -f $env:PYTHON_PIP_VERSION); \
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; \
	Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'; \
	\
	C:\Python64\python get-pip.py --disable-pip-version-check --no-cache-dir --no-warn-script-location; \
	Write-Host 'Verifying 64 bit pip install ...'; \
	C:\Python64\Scripts\pip --version; \
	\
	C:\Python32\python get-pip.py --disable-pip-version-check --no-cache-dir --no-warn-script-location; \
	Write-Host 'Verifying 32 bit pip install ...'; \
	C:\Python32\Scripts\pip --version; \
	\
	Remove-Item get-pip.py -Force; \
	\
	Write-Host 'Preparing 64 bit environment...'; \
	C:\Python64\Scripts\pip install -r requirements.txt --no-warn-script-location; \
	\
	Write-Host 'Preparing 32 bit environment...'; \
	C:\Python32\Scripts\pip install -r requirements.txt --no-warn-script-location; \
	\
	Write-Host 'Complete.';

CMD ["powershell", ".\\build.ps1", "latest"]
