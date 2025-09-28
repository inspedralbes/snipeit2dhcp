import os
import requests
import ast
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
NETWORK_BASE = os.getenv("NETWORK_BASE", "192.178")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "dhcpd.conf")
CUSTOM_POSITION_FIELD = os.getenv("CUSTOM_POSITION_FIELD", "Posició")
CUSTOM_MAC_FIELD = os.getenv("CUSTOM_MAC_FIELD", "Adreça MAC")  

LOCATIONS_LIST_str = os.getenv("LOCATIONS_LIST", "")

if LOCATIONS_LIST_str:
    try:
        print(f"Parsing LOCATIONS_LIST_str: {LOCATIONS_LIST_str}")
        locations = ast.literal_eval(f"[{LOCATIONS_LIST_str}]")
    except Exception as e:
        print(f"Error parsing LOCATIONS_LIST: {e}")
        exit(1)
        
else:
    locations = []



def posicio_a_ip(last_octet_str):
    """
    Converteix un valor com 'A1', 'B5' en un número per a l'últim octet de la IP.
    """
    if not last_octet_str:
        return None

    col = last_octet_str[0].upper()  # lletra
    row = last_octet_str[1:]         # número
    if not row.isdigit():
        return None

    base = (ord(col) - ord('A') + 1) * 10 +100  # A=100, B=200, C=300...
    return base + int(row)





headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

#Otenir tots els actius de Snipe-IT
# d'una location passada per id
def obtenir_assets(location_id):
    assets = []
    url = f"{API_URL}/api/v1/hardware"
    params = {"limit": 5,
              "location_id": location_id
              } 
    while url:
        r = requests.get(url, headers=headers, params=params, verify=False)
        r.raise_for_status()
        data = r.json()
        assets.extend(data.get("rows", []))
        url = data.get("next")  # si hi ha més pàgines
        params = None           # només a la primera crida

    return assets




def generar_dhcpd(assets, lan_id):    
    with open(OUTPUT_FILE, "a") as f:
        f.write("# Fitxer generat automàticament per snipeit2dhcp\n\n")
        for asset in assets:

            mac = (
                asset.get("custom_fields", {})
                     .get(CUSTOM_MAC_FIELD, {})
                     .get("value")
            )

            position = (
                asset.get("custom_fields", {})
                     .get(CUSTOM_POSITION_FIELD, {})
                     .get("value")
            )

            f.write("# ID: " + str(asset.get("id", "Sense ID")) + " // " + (str(position) if position is not None else "--") + "\n")
            f.write("# Tag: " + asset.get("asset_tag", "Sense Tag") + "\n")
            f.write("# Location: " + (asset.get("location", {}).get("name", "Sense Location") if asset.get("location") else "Sense Location") + "\n")
            f.write("# " + asset.get("model", {}).get("name", "Sense model") + "\n")
        
            name = asset.get("asset_tag")

            if mac and position:
                ip = f"{NETWORK_BASE}.{lan_id}.{posicio_a_ip(position)}"
                f.write(f"host {name} {{\n")
                f.write(f"  hardware ethernet {mac};\n")
                f.write(f"  fixed-address {ip};\n")
                f.write("}\n\n")
            else:
                f.write(f"# Atenció: Equip sense @MAC o sense posició \n\n")




if __name__ == "__main__":
    with open(OUTPUT_FILE, "w") as f:
        f.write("") # netejar el fitxer abans de començar

    for pos, lan in locations:
        print(f"Generant DHCP per la localització {pos} (ID {lan})...")
        assets = obtenir_assets(pos)
        generar_dhcpd(assets,lan)
    print(f"Fitxer DHCP generat: {OUTPUT_FILE}")
