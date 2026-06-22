# 🛠️ Cc-Checker-MrCardChecker

[![Website](https://img.shields.io/badge/Website-mrcardchecker.live-blue?style=flat&logo=google-chrome)](https://mrcardchecker.live)
[![Telegram](https://img.shields.io/badge/Telegram-Admin_Support-0088cc?style=flat&logo=telegram)](https://t.me/mrcardcheckeradmin_new)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Kali%20Linux-red.svg)](https://www.kali.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An advanced, lightweight Python-based Command Line Interface (CLI) web automation tool specifically designed for **Kali Linux** environments. This tool integrates seamlessly with the **[MrCardChecker.live](https://mrcardchecker.live)** platform to perform asynchronous web-based validations and stream results directly back to your local environment.

---

## 📌 Key Features (Synced with Web Infrastructure)

* **Luhn Algorithm Validation:** Instantly checks if the format passes the standard MOD 10 checksum to eliminate basic typos before processing.
* **BIN / IIN Lookup System:** Automatically identifies the card network (Visa, Mastercard, Amex, etc.), card type (Credit/Debit/Prepaid), issuing bank, and country of origin.
* **Live / Die Gate Simulation:** Integrates with the platform's core multi-gate processing structure to evaluate live operational statuses.
* **Batch Processing & CLI Optimization:** Tailored for security researchers and developers to sequentially validate bulk lists within the terminal.

---

## 🏗️ Workflow & Architecture

1. **Local Initialization:** Run the CLI script on your Kali Linux environment.
2. **Data Ingestion:** The script parses data formats (`NUMBER|MM|YY|CVV`).
3. **API Synchronicity:** Dispatches payload streams to the authorized production gateway endpoints at `mrcardchecker.live`.
4. **Structured Output:** Categorizes response statuses into clear structural mappings (`Live`, `Declined`, or `Unknown/Invalid`) in real time.

---

## 🚀 Getting Started

### Prerequisites
Make sure your system has Python 3 and the necessary dependencies installed:

```bash
pip install requests
