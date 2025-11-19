pipeline {
  agent any

  environment {
    // GNS3 / lab parameters
    LAB_NAME       = "cit480-operation-nightingale-${BUILD_NUMBER}"
    CLOUD_INIT_DIR = "/mnt/roseaw/cloud-init"

    // SIEM / Splunk parameters
    SOC_SIEM_IP    = "10.99.10.20"
    SPLUNK_TGZ_URL = "https://download.splunk.com/products/splunk/releases/9.2.0/linux/splunk-9.2.0-a1234567890-Linux-x86_64.tgz"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('NFS Health Check (/mnt/roseaw)') {
      steps {
        sh '''
          echo "[*] Checking NFS mount at /mnt/roseaw..."

          if ! mountpoint -q /mnt/roseaw; then
            echo "[!] /mnt/roseaw is not a mountpoint."
            echo "    Make sure NFS is mounted with:"
            echo "      sudo mkdir -p /mnt/roseaw"
            echo "      sudo mount -t nfs 10.48.228.25:/srv/nfs/roseaw /mnt/roseaw"
            exit 1
          fi

          echo "[*] /mnt/roseaw is mounted:"
          mount | grep /mnt/roseaw || true

          echo "[*] Testing write permissions to ${CLOUD_INIT_DIR}..."
          mkdir -p "${CLOUD_INIT_DIR}"
          touch "${CLOUD_INIT_DIR}/.jenkins_nfs_test" || {
            echo "[!] Jenkins cannot write to ${CLOUD_INIT_DIR}."
            exit 1
          }
          rm -f "${CLOUD_INIT_DIR}/.jenkins_nfs_test"

          echo "[✓] NFS health check passed. ${CLOUD_INIT_DIR} is writable."
        '''
      }
    }

    stage('Build GNS3 Topology + Generate Cloud-Init ISOs') {
      steps {
        sh '''
          echo "[*] LAB_NAME     = ${LAB_NAME}"
          echo "[*] CLOUD_INIT_DIR = ${CLOUD_INIT_DIR}"
          echo "[*] Bootstrapping pip locally (if needed)..."

          if ! python3 -m pip --version >/dev/null 2>&1; then
            curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py --user
          fi

          echo "[*] Installing Python dependencies (with pydantic<1.10)..."
          # requirements.txt should include something like:
          #   gns3fy>=0.8.0
          #   requests>=2.31.0
          #   pydantic<1.10
          python3 -m pip install --user --upgrade --force-reinstall -r requirements.txt

          echo "[*] Building CIT480 Operation Nightingale GNS3 topology..."
          # build_cit480_topology.py should:
          # - read LAB_NAME from env
          # - connect to GNS3 servers
          # - create all nodes/links
          # - generate per-node cloud-init YAML + seed ISOs into CLOUD_INIT_DIR
          LAB_NAME="${LAB_NAME}" CLOUD_INIT_DIR="${CLOUD_INIT_DIR}" python3 build_cit480_topology.py
        '''
      }
    }

    stage('Verify Cloud-Init ISOs on NFS') {
      steps {
        sh '''
          echo "[*] Verifying cloud-init seed ISOs in ${CLOUD_INIT_DIR}..."

          if ! ls "${CLOUD_INIT_DIR}"/*.iso >/dev/null 2>&1; then
            echo "[!] No .iso files found in ${CLOUD_INIT_DIR}."
            echo "    Expected per-node seed ISOs like:"
            echo "      ${CLOUD_INIT_DIR}/soc-siem-01-seed.iso"
            echo "      ${CLOUD_INIT_DIR}/cloud-web-01-seed.iso"
            exit 1
          fi

          echo "[*] Found the following seed ISOs:"
          ls -1 "${CLOUD_INIT_DIR}"/*.iso

          echo "[✓] Cloud-init ISOs are present on NFS and ready for GNS3 VMs."
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
            echo "[*] Waiting 90 seconds for soc-siem-01 (${SOC_SIEM_IP}) to boot..."
            sleep 90

            echo "[*] Copying Splunk install script to SIEM..."
            sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no \
              scripts/install_splunk_siem.sh \
              ${SSH_USER}@${SOC_SIEM_IP}:/tmp/install_splunk_siem.sh

            echo "[*] Running Splunk install script on SIEM..."
            sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no \
              ${SSH_USER}@${SOC_SIEM_IP} "
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
      echo "✅ GNS3 lab built, cloud-init ISOs present on NFS, and native Splunk started on soc-siem-01 (${SOC_SIEM_IP})."
      echo "   Splunk Web should be available at: http://${SOC_SIEM_IP}:8000"
    }
    failure {
      echo "❌ Pipeline failed — check console output for NFS, GNS3, or Splunk errors."
    }
  }
}
