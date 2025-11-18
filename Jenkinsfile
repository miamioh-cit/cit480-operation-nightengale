pipeline {
  agent any

  environment {
    SOC_SIEM_IP = "10.99.10.20"
    SPLUNK_TGZ_URL = "https://download.splunk.com/products/splunk/releases/9.2.0/linux/splunk-9.2.0-a1234567890-Linux-x86_64.tgz"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build GNS3 Topology') {
      steps {
        sh '''
          echo "[*] Bootstrapping pip locally..."
          curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
          python3 get-pip.py --user
    
          echo "[*] Installing Python dependencies..."
          ~/.local/bin/pip3 install --user -r requirements.txt
    
          echo "[*] Building CIT480 Operation Nightingale GNS3 topology..."
          ~/.local/bin/python3 build_cit480_topology.py
        '''
      }
    }



    stage('Install & Start Splunk on SIEM') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'siem-ubuntu-creds',
          usernameVariable: 'SSH_USER',
          passwordVariable: 'SSH_PASS'
        )]) {
          sh '''
            echo "[*] Waiting 90s for soc-siem-01 to boot..."
            sleep 90

            echo "[*] Copying Splunk install script to SIEM..."
            sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no               scripts/install_splunk_siem.sh               ${SSH_USER}@${SOC_SIEM_IP}:/tmp/install_splunk_siem.sh

            echo "[*] Running Splunk install script on SIEM..."
            sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no               ${SSH_USER}@${SOC_SIEM_IP} "
                chmod +x /tmp/install_splunk_siem.sh
                SPLUNK_TGZ_URL='${SPLUNK_TGZ_URL}' /tmp/install_splunk_siem.sh
              "
          '''
        }
      }
    }
  }

  post {
    success {
      echo "✅ GNS3 lab built and native Splunk started on soc-siem-01 (${SOC_SIEM_IP})."
      echo "   Splunk Web: http://${SOC_SIEM_IP}:8000"
    }
    failure {
      echo "❌ Pipeline failed — check console output for GNS3 or Splunk errors."
    }
  }
}
