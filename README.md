# Akamai Product Migration Script

This script automates changing the **Akamai product** for a list of properties and optionally activates the new version to **Staging** or **Production**.

---

## 📦 Prerequisites

- Python 3.x installed
- Install required libraries:

```bash
pip install requests pandas akamai-edgegrid
```

- Add the below details to  `akamai_config.py` file with the following contents:

```python
akatoken = 'your_akatoken'
akasso = 'your_akasso'
xsrf_token = 'your_xsrf_token'
accountSwitchKey = 'your_accountSwitchKey'
edgerc_location = '/path/to/.edgerc'
activation_emails = 'default_email@example.com'
reviewer_email = 'default_reviewer@example.com'
```

- Use a `configlist.xls` file containing two columns:
  - **Property**: Akamai property name
  - **Target Product**: New product name (must match predefined mappings)

---

## 🚀 How to Run

```bash
python3 prod_change.py [options]
```

### Options:

| Option | Description |
|:-------|:------------|
| `--save` | Only save the new version without activating |
| `--activate-to-staging` | Activate the new version to **Staging** |
| `--activate-to-production` | Activate the new version to **Production** (you will be prompted for emails) |

---

## 📄 Example Usage

Save only (no activation):

```bash
python3 prod_change.py --save
```

Save and activate to staging:

```bash
python3 prod_change.py --activate-to-staging
```

Save and activate to production (with email prompts):

```bash
python3 prod_change.py --activate-to-production
```

---

## ✨ Notes

- If you activate to production, you will be prompted to input:
  - Activation Email(s)
  - Reviewer Email (for compliance record)
- All logs are printed to the console with timestamps.


---
