aws dynamodb query `
    --table-name core-automation-portfolios `
    --key-condition-expression "#cp = :client and #p = :portfolio" `
    --expression-attribute-names '{"#cp": "client", "#p": "portfolio"}' `
    --expression-attribute-values '{":client":{"S":"eits"}, ":portfolio":{"S":"simple-cloud-kit"}}' `
    --output json
