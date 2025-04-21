DOCKER  ?= sudo podman
SECRET_TEMPDIR ?= ./.secrets
SECRET_PATH ?= 'secret/scs/github/pat'
PYTHON_EXE ?= python3.9
VENV_DIR ?= ./.venv
REPONAME ?= slaclab
IMAGENAME ?= s3-bucket-usage-exporter
TAG ?= latest


secrets:
	mkdir -p $(SECRET_TEMPDIR)
	set -e; for i in $(SECRET_KEYS); do vault kv get --field=$$i $(SECRET_PATH) > $(SECRET_TEMPDIR)/$$i ; done

clean-secrets:
	rm -rf $(SECRET_TEMPDIR)



build:
	$(DOCKER) build . -t $(REPONAME)/$(IMAGENAME):$(TAG)

push:
	$(DOCKER) push $(REPONAME)/$(IMAGENAME):$(TAG)
	
venv:
	mkdir -p .venv
	$(PYTHON_EXE) -m venv ./.venv

clean-venv:
	rm -rf $(VENV_DIR)

pip:
	$(VENV_DIR)/bin/pip3 install --upgrade pip
	$(VENV_DIR)/bin/pip3 install -r requirements.txt

devenv: venv pip

black:
	$(VENV_DIR)/bin/black ./

clean: clean-secrets clean-venv

try:
	$(VENV_DIR)/bin/python s3-bucket-usage-exporter.py
