import os
import requests
from dotenv import load_dotenv


# Per començar, copia .env.example a .env i edita les variables segons el teu entorn.

# Crea un entorn virtual (opcional però recomanat):
# apt install python3.12-venv
# python3 -m venv venv
# source venv/bin/activate   (o venv\Scripts\activate a Windows)



# i després instal·la les dependències:
# pip install -r requirements.txt


# Carregar variables d'entorn des del fitxer .env
load_dotenv()

API_URL = os.getenv("SNIPEIT_URL")
API_TOKEN = os.getenv("SNIPEIT_TOKEN")
NETWORK_BASE = os.getenv("NETWORK_BASE", "192.168.10.")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "dhcpd.conf")
CUSTOM_FIELD = os.getenv("CUSTOM_FIELD", "Ultim_Octet")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

def obtenir_assets():
    assets = []
    url = f"{API_URL}/api/v1/hardware"
    params = {"limit": 2,
              "location": 23
              } 
    while url:
        r = requests.get(url, headers=headers, params=params, verify=False)
        r.raise_for_status()
        data = r.json()
        assets.extend(data.get("rows", []))
        url = data.get("next")  # si hi ha més pàgines
        params = None           # només a la primera crida

    return assets

def generar_dhcpd(assets):
    with open(OUTPUT_FILE, "w") as f:
        for asset in assets:
            mac = asset.get("mac_address")
            last_octet = (
                asset.get("custom_fields", {})
                     .get(CUSTOM_FIELD, {})
                     .get("value")
            )
            name = asset.get("name")

            if mac and last_octet:
                ip = f"{NETWORK_BASE}{last_octet}"
                f.write(f"host {name} {{\n")
                f.write(f"  hardware ethernet {mac};\n")
                f.write(f"  fixed-address {ip};\n")
                f.write("}\n\n")

if __name__ == "__main__":
    assets = obtenir_assets()
    generar_dhcpd(assets)
    print(f"Fitxer DHCP generat: {OUTPUT_FILE}")
