targetScope = 'resourceGroup'

param location string = resourceGroup().location
param containerImageName string = 'infrastructure-agent:latest'
param registryName string
param openAiEndpoint string
param keyVaultName string

// Container Apps Environment
resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-infrastructure-agent'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
    }
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-infrastructure-agent'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
      }
      secrets: [
        {
          name: 'openai-key'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/openai-key'
          identity: 'system'
        }
        {
          name: 'github-token'
          keyVaultUrl: '${keyVault.properties.vaultUri}secrets/github-token'
          identity: 'system'
        }
      ]
      registries: [
        {
          server: '${registryName}.azurecr.io'
          identity: 'system-environment'
        }
      ]
    }
    template: {
      containers: [
        {
          image: '${registryName}.azurecr.io/${containerImageName}'
          name: 'infrastructure-agent'
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'openai-key'
            }
            {
              name: 'GITHUB_TOKEN'
              secretRef: 'github-token'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyVaultName
}

// Grant Container App access to Key Vault
resource keyVaultAccess 'Microsoft.KeyVault/vaults/accessPolicies@2023-02-01' = {
  parent: keyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        objectId: containerApp.identity.principalId
        tenantId: subscription().tenantId
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
  }
}

output appUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'