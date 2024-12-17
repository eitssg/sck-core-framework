aws dynamodb query `
    --table-name core-automation-apps `
    --key-condition-expression "#cp = :client_portfolio and #rx = :rx" `
    --expression-attribute-names '{"#cp": "client-portfolio", "#rx": "app-regex"}' `
    --expression-attribute-values '{":client_portfolio":{"S":"eits:simple-cloud-kit"}, ":rx":{"S":"^api:[^:]+:[^:]+$"}}' `
    --output json
