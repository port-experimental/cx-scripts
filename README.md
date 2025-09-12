# Port Customer Experience Scripts

![port-oss-category](https://github.com/port-experimental/oss-images/blob/main/example-code.png)

This is a list of code examples and scripts compiled by Port teams for the purpose of solving specific use cases raised by customers.

# Scripts
## Utilities
- [Port Audit Log Exporter to Kafka](https://github.com/port-experimental/audit-logs-to-kafka)
  - Streams Port audit logs directly into Kafka topics.
- [Deep Copy of Entities across Port orgs](https://github.com/port-experimental/deep-copy-entities)
  - Recursively copies Port entities between separate environments.
- [Parse Monorepo](https://github.com/port-experimental/parse-monorepo)
  - Parses monorepos to extract and analyze project structure.
- [Port Blueprint Cleaner](https://github.com/port-experimental/port-blueprint-cleaner)
  - Cleans and tidies unused Port blueprint configurations.
- [Compare Port Organizations](https://github.com/port-experimental/port_organization_comparison)
  - Compares configurations between two Port organizations programmatically.
- [Port Schemas Backup](https://github.com/port-experimental/port-schemas-backup)
  - Exports and backs up Port schema definitions safely.
- [PyPort - Port API Wrapper](https://github.com/port-experimental/PyPort)
  - Python wrapper for easy integration with Port's API.
- [Surveys to Excel](https://github.com/port-experimental/surveys-to-excel)
  - Converts Port survey results into formatted Excel sheets
- [Repo to Team Mapper](https://github.com/port-experimental/repo-team-mapper)
  - Maps GitHub repository ownership to corresponding Port teams.
- [Port Entity Exporter](https://github.com/port-experimental/entity-exporter.git)
  - Exports all entities to JSON,YAML, or CSV .
- [Port Integration Refresh](scripts/port-integration-refresh.py)
  - Triggers a refresh/resync of a Port integration.
- [GitHub User to Port User Mapping](scripts/map_users.py)
  - Maps GitHub user entities in Port to their corresponding general Port user entities.
- [Delete Datasource Entities](https://github.com/port-experimental/delete-datasource-entities)
  - Helps you delete all entities of a certain data source, from all blueprints.
- [Port YAML Validator](https://github.com/port-experimental/blueprint-yml-validator)
 - A tool for validating YAML files against Port's API.
- [TechDoc Experiement](https://github.com/port-experimental/techdoc-experiment)
  - Framework for ingesting documentation from various sources into a Port software catalog.

## Developer experience
- [Developer Onboarding Metrics](https://github.com/port-experimental/github-metrics)
  - Tracks and visualizes developer onboarding performance metrics.
- [GitHub Copilot Utilization](https://github.com/port-experimental/github-copilot-utilization)
  - Imports GitHub Copilot usage data into Port dashboards.
- [Self Service Actions ROI](https://github.com/port-experimental/actions-experience)
  - Backend for Self Service Actions ROI Experience. 

## Port as IaC
- [Terraform Import Generator](https://github.com/port-experimental/terraform-import-generator)
  - Automatically generates Terraform import scripts from Port.
- [Pulumi Import Generator](https://github.com/port-experimental/pulumi_import_generator)
  - Generates Pulumi import definitions based on Port resources.
- [Terraform Cloud State Parser](https://github.com/port-experimental/terraform-cloud-state-parser)
  - Parses state files from Terraform Cloud to generate resources and sync them to Port.

## Azure DevOps
- [Map Azure DevOps Teams to Port Users](https://github.com/port-experimental/map-ado-teams-to-port-user)
  - Syncs ADO teams with Port user accounts.
- [Azure DevOps Gradle Importer](https://github.com/port-experimental/gradle-importer)
  - Imports ADO Gradle project metadata into Port.
- [Azure Pipelines to Azure Repos connector in Port](https://github.com/port-experimental/connect-ado-pipelines)
  - Integrates ADO Pipelines with Port repositories.
- [Azure Devops Environments Fetcher](https://github.com/port-experimental/azure-devops-environments)
  - Syncs Azure Devops Environments and Deployments to Port.
- [Azure DevOps Tests & Code Coverage Analysis Integration](https://github.com/port-experimental/azure-devops-tests-and-code-coverage)
  - Script for ingests ADO tests and code coverage analysis into Port.

## Entra ID
- [Entra ID Provisioner to Port](https://github.com/port-experimental/entra-id-provisioner)
  - Provisions Entra (Azure AD) identities into Port automatically.

## Aikido
- [Aikido Integration](https://github.com/port-experimental/aikido-integration)
  - Bridges Aikido workflows into the Port ecosystem.

## Kong
- [Kong Konnect Ingestion](https://github.com/port-experimental/kong-konnect-ingestion)
  -  Ingests Kong Konnect API metrics into Port.

## JFrog
- [JFrog Exporter](https://github.com/port-experimental/jfrog-exporter)
  - Exports JFrog (Artifactory) data into Port-compatible format.

## GitLeaks
- [GitLeaks Port Demo](https://github.com/port-experimental/gitleaks-port-demo)
  - Demonstrates GitLeaks integration within Port contexts.

## Teamform
- [Teamform Integration](https://github.com/port-experimental/teamform)
  - A basic integration with teamform to ingest team hierarchies.

## Armorcode
- [Armorcode Integration](https://github.com/port-experimental/armorcode-integration)
  - Script to ingest Armorcode vulnerabilities and data.

## Cursor
- [Cursor Metrics](https://github.com/port-experimental/cursor-utilization)
 - Import Cursor Admin API metrics into Port as daily records (org + user) with event counts, line counts, and cost metrics.

## BugCrowd
- [BugCrowd Integration](https://github.com/port-experimental/bugcrowd-integration)
  - Scripts integration with bugcrowd to map bugcrowd submissions and programs to Port.
