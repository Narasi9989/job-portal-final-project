#!/bin/bash

# Jenkins Setup and Configuration Script
# This script helps configure Jenkins for the Job Portal CI/CD pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script variables
JENKINS_HOME="${JENKINS_HOME:-.}"
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_ADMIN_USER="admin"

echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}  Jenkins Job Portal CI/CD Setup${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Jenkins CLI access
if ! command -v java &> /dev/null; then
    echo -e "${RED}✗ Java not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Java is installed${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
fi

echo ""
echo -e "${YELLOW}Creating Jenkins configuration directories...${NC}"

# Create Jenkins configuration directory structure
mkdir -p "${JENKINS_HOME}/init.groovy.d"
mkdir -p "${JENKINS_HOME}/jobs"
mkdir -p "${JENKINS_HOME}/credentials"
mkdir -p "${JENKINS_HOME}/plugins"

echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo -e "${YELLOW}Setting up Jenkins system configuration...${NC}"

# Create Jenkins system configuration script
cat > "${JENKINS_HOME}/init.groovy.d/001-system-config.groovy" << 'EOF'
import jenkins.model.Jenkins
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import org.jenkinsci.plugins.matrixauth.authorization.ProjectMatrixAuthorizationStrategy

// Configure Jenkins security
def instance = Jenkins.getInstance()
def realm = new HudsonPrivateSecurityRealm(false)
instance.setSecurityRealm(realm)

// Configure authorization strategy
def strategy = new ProjectMatrixAuthorizationStrategy()
strategy.add("hudson.model.Item.Build", "authenticated")
strategy.add("hudson.model.Item.Cancel", "authenticated")
strategy.add("hudson.model.Item.Read", "authenticated")
strategy.add("hudson.model.Run.Delete", "authenticated")
strategy.add("hudson.model.Run.Update", "authenticated")
instance.setAuthorizationStrategy(strategy)

instance.save()
println("Jenkins security configuration applied")
EOF

echo -e "${GREEN}✓ System configuration created${NC}"

echo ""
echo -e "${YELLOW}Setting up Jenkins credentials configuration...${NC}"

# Create credentials setup script
cat > "${JENKINS_HOME}/init.groovy.d/002-credentials-setup.groovy" << 'EOF'
import jenkins.model.Jenkins
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import hudson.util.Secret

// Get Jenkins instance
def jenkins = Jenkins.getInstance()
def credentialsStore = jenkins.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
def domain = Domain.global()

// Function to check if credential already exists
def credentialExists(credentialsStore, credentialId) {
    return credentialsStore.getCredentials(domain).any { it.id == credentialId }
}

// Function to create credentials
def createUsernamePasswordCredential(store, credentialId, username, password, description) {
    if (!credentialExists(store, credentialId)) {
        def credentials = new UsernamePasswordCredentialsImpl(
            CredentialsScope.GLOBAL,
            credentialId,
            description,
            username,
            password
        )
        store.addCredentials(domain, credentials)
        println("Created credential: ${credentialId}")
    } else {
        println("Credential already exists: ${credentialId}")
    }
}

def createSecretCredential(store, credentialId, secret, description) {
    if (!credentialExists(store, credentialId)) {
        def credentials = new StringCredentialsImpl(
            CredentialsScope.GLOBAL,
            credentialId,
            description,
            Secret.fromString(secret)
        )
        store.addCredentials(domain, credentials)
        println("Created secret: ${credentialId}")
    } else {
        println("Secret already exists: ${credentialId}")
    }
}

// Create Docker Registry credentials
createUsernamePasswordCredential(credentialsStore, "docker-registry-credentials", 
    System.getenv("DOCKER_REGISTRY_USERNAME") ?: "your-docker-username",
    System.getenv("DOCKER_REGISTRY_PASSWORD") ?: "your-docker-password",
    "Docker Registry Credentials")

// Create Oracle Database credentials
createUsernamePasswordCredential(credentialsStore, "oracle-user", 
    System.getenv("ORACLE_USER") ?: "narasimha",
    System.getenv("ORACLE_PASSWORD") ?: "narasimha",
    "Oracle Database Credentials")

// Create Slack webhook
createSecretCredential(credentialsStore, "slack-webhook-url",
    System.getenv("SLACK_WEBHOOK_URL") ?: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "Slack Webhook URL")

// Create GitHub token (if using GitHub)
createSecretCredential(credentialsStore, "github-token",
    System.getenv("GITHUB_TOKEN") ?: "your-github-token",
    "GitHub Personal Access Token")

jenkins.save()
println("Credentials configuration completed")
EOF

echo -e "${GREEN}✓ Credentials configuration created${NC}"

echo ""
echo -e "${YELLOW}Setting up Jenkins pipeline job...${NC}"

# Create pipeline job configuration
cat > "${JENKINS_HOME}/jobs/JobPortal-Pipeline/config.xml" << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@1360.v0c46188b_0aeb_">
  <actions/>
  <description>Job Portal CI/CD Pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coralogix.jenkins.plugin.CoralogixProperties plugin="coralogix@1.4.7"/>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps@3857.v6a_cceb_a_ed47e">
    <scm class="hudson.plugins.git.GitSCM" plugin="git@5.0.0">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>${GIT_REPO_URL}</url>
          <credentialsId>github-credentials</credentialsId>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="java.util.ArrayList"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

echo -e "${GREEN}✓ Pipeline job configuration created${NC}"

echo ""
echo -e "${YELLOW}Installing required Jenkins plugins...${NC}"

# List of required plugins
PLUGINS=(
    "pipeline:4851.v37c2e3d17dc2"
    "docker-workflow:563.vd602cc813a84"
    "docker:1.2.10"
    "git:5.0.0"
    "github:1.39.0"
    "slack:678.v03a_1f5b_03b_f1"
    "email-ext:2.104"
    "junit:1184.va_a_9d8a_882e45"
    "cobertura:1.17"
)

echo -e "${YELLOW}Plugins to install:${NC}"
for plugin in "${PLUGINS[@]}"; do
    echo "  - $plugin"
done

echo ""
echo -e "${YELLOW}Note: Plugins can be installed via Jenkins UI or using jenkins-cli${NC}"
echo -e "${YELLOW}Jenkins UI: Manage Jenkins → Plugin Manager${NC}"

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}  Jenkins Setup Completed!${NC}"
echo -e "${GREEN}===============================================${NC}"

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Access Jenkins at: ${JENKINS_URL}"
echo "2. Log in with admin credentials"
echo "3. Install recommended plugins (if not auto-installed)"
echo "4. Create/configure credentials in Jenkins UI"
echo "5. Create new Pipeline job with this configuration:"
echo "   - Repository URL: <your-git-repo>"
echo "   - Script Path: Jenkinsfile"
echo "6. Run the pipeline: Build Now"

echo ""
echo -e "${YELLOW}Required Credentials to Create:${NC}"
echo "1. docker-registry-credentials (Username/Password)"
echo "2. oracle-user (Username/Password)"
echo "3. slack-webhook-url (Secret text)"
echo "4. github-token (Secret text, optional)"

echo ""
echo -e "${YELLOW}Environment Variables to Set:${NC}"
echo "1. ORACLE_USER=${ORACLE_USER}"
echo "2. ORACLE_PASSWORD=${ORACLE_PASSWORD}"
echo "3. DOCKER_REGISTRY=${DOCKER_REGISTRY}"
echo "4. SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}"

echo ""
echo -e "${YELLOW}Useful Jenkins CLI Commands:${NC}"
echo "# Download Jenkins CLI"
echo "wget http://localhost:8080/jnlpJars/jenkins-cli.jar"
echo ""
echo "# Create job from XML"
echo "java -jar jenkins-cli.jar -s http://localhost:8080 create-job JobPortal-Pipeline < config.xml"
echo ""
echo "# Trigger build"
echo "java -jar jenkins-cli.jar -s http://localhost:8080 build JobPortal-Pipeline"
echo ""
echo "# Get job status"
echo "java -jar jenkins-cli.jar -s http://localhost:8080 get-job JobPortal-Pipeline"

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
