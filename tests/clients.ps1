aws dynamodb query `
    --table-name core-automation-clients `
    --key-condition-expression "#cp = :client" `
    --expression-attribute-names '{"#cp": "client"}' `
    --expression-attribute-values '{":client":{"S":"eits"}}' `
    --output json
