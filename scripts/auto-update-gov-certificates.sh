#!/bin/sh

# This script adds to the system certificates the government ones that are necessary
# for the validation of the digital certificate present on the TS-CNS Smart Card.
#
# Execute this bash script with sudo command

if [ `whoami` != root ]; then
    echo Please run this script as root or using sudo
    exit
fi

LOG_FILE="/var/log/auto-update-gov-certificates.log"
touch "${LOG_FILE}"

# Env for Trusted CA certificate
export GOV_TRUST_CERTS_SERVICE_TYPE_IDENTIFIER=http://uri.etsi.org/TrstSvc/Svctype/IdV
export GOV_TRUST_CERTS_OUTPUT_TEMP_PATH=/tmp/gov/trust/certs
export GOV_TRUST_CERTS_OUTPUT_PATH=/usr/local/share/ca-certificates

echo "$(date "+%FT%T") Start auto upgrade Gov Certificates..." >> "${LOG_FILE}"

echo "$(date "+%FT%T") Remove temporary certificates file from ${GOV_TRUST_CERTS_OUTPUT_TEMP_PATH}" >> "${LOG_FILE}"
rm -rf "${GOV_TRUST_CERTS_OUTPUT_TEMP_PATH}"

echo "$(date "+%FT%T") Downloading Gov Certificates..." >> "${LOG_FILE}"
./parse-gov-certs.py \
    --output-folder ${GOV_TRUST_CERTS_OUTPUT_TEMP_PATH} \
    --service-type-identifier ${GOV_TRUST_CERTS_SERVICE_TYPE_IDENTIFIER}

echo "$(date "+%FT%T") Downloading Gov Certificates...[END]" >> "${LOG_FILE}"

echo "$(date "+%FT%T") Save Gov Certificates into ${GOV_TRUST_CERTS_OUTPUT_TEMP_PATH}" >> "${LOG_FILE}"
echo "$(date "+%FT%T") Copy Gov Certificates into ${GOV_TRUST_CERTS_OUTPUT_PATH}" >> "${LOG_FILE}"
cp "${GOV_TRUST_CERTS_OUTPUT_TEMP_PATH}"/*.crt "${GOV_TRUST_CERTS_OUTPUT_PATH}"

echo "$(date "+%FT%T") Re-Hashing ${GOV_TRUST_CERTS_OUTPUT_PATH}..." >> "${LOG_FILE}"
c_rehash ${GOV_TRUST_CERTS_OUTPUT_PATH}

echo "$(date "+%FT%T") Start auto upgrade Gov Certificates...[END]" >> "${LOG_FILE}"

echo "$(date "+%FT%T") Run update-ca-certificates..." >> "${LOG_FILE}"
update-ca-certificates