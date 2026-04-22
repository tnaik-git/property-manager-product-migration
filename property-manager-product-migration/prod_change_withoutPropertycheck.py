import requests
import argparse
import time
import json
import logging
import pandas as pd
from akamaiproperty import AkamaiProperty
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from akamai_config import akatoken, akasso, xsrf_token, accountSwitchKey, edgerc_location, activation_emails, reviewer_email

# Setup logger
logger = logging.getLogger("akamai_product_change")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Change Akamai property product and optionally activate.')
parser.add_argument('--save', action='store_true', help='Only save the new version without activation')
parser.add_argument('--activate-to-staging', action='store_true', help='Activate the version to Staging')
parser.add_argument('--activate-to-production', action='store_true', help='Activate the version to Production')
args = parser.parse_args()

# If activating to production, ask user for emails
if args.activate_to_production:
    activation_emails = input("Enter activation email(s) for Production (comma-separated): ").strip()
    reviewer_email = input("Enter reviewer email for compliance record: ").strip()

# Validate session cookies
cookies = {
    'AKATOKEN': akatoken,
    'AKASSO': akasso
}

headers = {
    'Content-Length': '0',
    'X-XSRF-TOKEN': xsrf_token
}

validate_response = requests.get(
    'https://control.akamai.com/dashboard-manager/v1/dashboard-config',
    headers=headers,
    cookies=cookies
)

if validate_response.status_code != 200:
    logger.error("❌ Your session cookies are invalid or expired. Please enter correct cookie details.")
    exit()

logger.info("✅ Your session cookies are valid. Proceeding ahead with the product change...")

# Setup EdgeGrid session
session = requests.Session()
session.auth = EdgeGridAuth.from_edgerc(edgerc_location, section='default')
session.headers.update({
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'PAPI-Use-Prefixes': 'true'
})
edgerc = EdgeRc(edgerc_location)
base_url = f"https://{edgerc.get('default', 'host')}"

# Mapping of human-readable product names to API codes
product_map = {
    'Adaptive Media Delivery': 'Adaptive_Media_Delivery',
    'Object Delivery': 'Obj_Delivery',
    'Download Delivery': 'Download_Delivery',
    'Dynamic Site Delivery': 'Dynamic_Site_Del',
    'Wholesale Delivery': 'Wholesale_Delivery',
    'Dynamic Site Accelerator': 'Site_Accel',
    'Ion Standard': 'Fresca',
    'Ion Premiere': 'SPM',
    'Ion Media Advanced': 'RM',
    'Cloud Security Failover': 'Security_Failover',
    'Kona DDoS Defender': 'KDD',
    'Kona Site Defender': 'Site_Defender',
    'Rich Media Accelerator': 'Rich_Media_Accel'
}

# Load properties from Excel
df = pd.read_excel('/Users/tnaik/Downloads/MajorsAAP/IonPMigration/GeneralMotors/property-manager-product-migration/configlist_gm.xls')

# Process each property
for index, row in df.iterrows():
    config = "".join(str(row['Property']).split())
    target_product = str(row['Target Product']).strip()

    try:
        akam_config = AkamaiProperty(edgerc_location, config, accountSwitchKey)
        new_version = akam_config.createVersion(akam_config.getProductionVersion())
        akam_config.addVersionNotes(new_version, "Change Product type")

        accountId = accountSwitchKey.split(":")[0]
        params = {
            'accountId': accountId,
            'aid': akam_config.assetId[4:],
            'gid': akam_config.groupId[4:],
            'product': product_map[target_product],
            'v': str(new_version)
        }

        logger.info(f"🔄 Changing Product for {config} by creating new version {new_version}")

        #prod_change_url = 'https://control.akamai.com/pm-backend-blue/service/v1/properties/set_product'
        prod_change_url = 'https://control.akamai.com/pm-backend-green/service/v1/properties/set_product'

        response = requests.post(
            prod_change_url,
            headers=headers,
            params=params,
            cookies=cookies
        )

        logger.info("********************************************************************************")
        logger.info(f"Response Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        logger.info("********************************************************************************")

        if response.ok:
            logger.info(f"✅ Successfully changed the product for {config} to {target_product}")

            if not args.save:
                contract_id = akam_config.contractId.replace(",", "")
                group_id = akam_config.groupId.replace(",", "")
                property_id = akam_config.propertyId.replace(",", "")

                time.sleep(5)

                if args.activate_to_staging:
                    logger.info(f"🚀 Activating {config} version {new_version} to Staging...")
                    try:
                        activation_url = f"{base_url}/papi/v1/properties/{property_id}/activations"
                        query_params = {
                            "contractId": contract_id,
                            "groupId": group_id,
                            "accountSwitchKey": accountSwitchKey
                        }
                        activation_payload = {
                            "network": "STAGING",
                            "notifyEmails": activation_emails.split(','),
                            "acknowledgeAllWarnings": True,
                            "activationType": "ACTIVATE",
                            "note": "Product Migration",
                            "propertyVersion": int(new_version)
                        }
                        activation_response = session.post(activation_url, params=query_params, json=activation_payload)
                        if activation_response.status_code == 201:
                            logger.info(f"✅ Successfully activated {config} version {new_version} to Staging")
                        else:
                            logger.error(f"❌ Activation failed for {config} version {new_version}")
                            logger.error(f"Response: {activation_response.text}")
                    except Exception as e:
                        logger.error(f"❌ Activation error: {str(e)}")

                if args.activate_to_production:
                    logger.info(f"🚀 Activating {config} version {new_version} to Production...")
                    try:
                        activation_url = f"{base_url}/papi/v1/properties/{property_id}/activations"
                        query_params = {
                            "contractId": contract_id,
                            "groupId": group_id,
                            "accountSwitchKey": accountSwitchKey
                        }
                        activation_payload = {
                            "network": "PRODUCTION",
                            "notifyEmails": activation_emails.split(','),
                            "acknowledgeAllWarnings": True,
                            "activationType": "ACTIVATE",
                            "note": "Product Migration",
                            "propertyVersion": int(new_version),
                            "complianceRecord": {
                                "noncomplianceReason": "EMERGENCY",
                                "peerReviewedBy": reviewer_email,
                                "customerEmail": activation_emails.split(',')[0],
                                "unitTested": True
                            }
                        }
                        activation_response = session.post(activation_url, params=query_params, json=activation_payload)
                        if activation_response.status_code == 201:
                            logger.info(f"✅ Successfully activated {config} version {new_version} to Production")
                        else:
                            logger.error(f"❌ Activation failed for {config} version {new_version}")
                            logger.error(f"Response: {activation_response.text}")
                    except Exception as e:
                        logger.error(f"❌ Activation error: {str(e)}")

        else:
            logger.error(f"❌ Error changing the product for {config} to {target_product}")

    except Exception as e:
        logger.error(f"❌ Exception occurred while changing the product for {config} to {target_product}")
        logger.error('*' * 80)
        logger.error(f"Exception: {str(e)}")
