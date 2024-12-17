aws dynamodb query `
    --table-name core-automation-accounts `
    --key-condition-expression "#cp = :client_portfolio and #z = :zone" `
    --expression-attribute-names '{"#cp": "client-portfolio", "#z": "zone"}' `
    --expression-attribute-values '{":client_portfolio":{"S":"eits:simple-cloud-kit"}, ":zone":{"S":"simple-cloud-kit-prod"}}' `
    --output json
