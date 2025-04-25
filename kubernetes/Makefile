KUBECTL_DEPLOY_CONTEXT ?= 'sdf-monitoring'

ensure-context:
	if [ '$(shell kubectl config current-context)' != $(KUBECTL_DEPLOY_CONTEXT) ]; then echo "Configured deployment context incorrect; expecting $(KUBECTL_DEPLOY_CONTEXT)."; exit 1; fi

get-secrets: ensure-context
	mkdir -p ./etc/.secrets
	vault kv get --field=access_key secret/rubin/embargo/read/rubin-summit-users > ./etc/.secrets/access_key
	vault kv get --field=secret_key secret/rubin/embargo/read/rubin-summit-users > ./etc/.secrets/secret_key

clean-secrets:
	rm -rf etc/.secrets

run-apply:
	kubectl apply -k .

apply: get-secrets run-apply clean-secrets
