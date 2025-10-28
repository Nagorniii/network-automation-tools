from pynetbox import api
from dotenv import load_dotenv
from ipaddress import ip_network
import os

# ====== Підключення до NetBox ======
load_dotenv()
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = api(NETBOX_URL, token=NETBOX_TOKEN)

# ================= Функції =================

def view_prefixes():
    prefixes = nb.ipam.prefixes.all()
    if not prefixes:
        print("Префіксів немає.")
        return []
    print("\nСписок префіксів:")
    for p in prefixes:
        print(f"- {p.prefix} | {p.status} | {p.description}")
    return prefixes

def validate_prefix(prefix_str: str):
    try:
        return str(ip_network(prefix_str, strict=False))
    except ValueError:
        print("❌ Невірний формат префіксу.")
        return None


def create_prefix(prefix, description="Створено скриптом" ):
    prefix_valid = validate_prefix(prefix)
    if not prefix_valid:
        return None

    existing = nb.ipam.prefixes.get(prefix=prefix)
    if existing:
        print(f"❌ Префікс {prefix} вже існує.")
        return existing
    created = nb.ipam.prefixes.create(prefix=prefix, description=description, status="active")
    print(f"✅ Створено префікс {created.prefix}")
    return created


def create_ip_in_prefix(prefix_str, description="", dns_name="",  tags=None, ip_address=None, from_end=False):

    prefix = nb.ipam.prefixes.get(prefix=prefix_str)
    if not prefix:
        print(f"❌ Префікс {prefix_str} не знайдено.")
        return None

    available = prefix.available_ips.list()
    selected_ip = None

    if ip_address:
        selected_ip = ip_address
    else:
        if not available:
            print(f"⚠️ Вільних IP немає у {prefix_str}.")
            selected_ip = input("Введіть IP вручну: ").strip()
        else:
            # Показуємо перші або останні 5 IP залежно від from_end
            shown = list(reversed(available[-5:])) if from_end else available[:5]
            direction = "з кінця" if from_end else "з початку"
            print(f"\nВільні IP ({direction}):")
            for ip in shown:
                print(f"- {ip['address']}")

            user_input = input("Введіть IP вручну або Enter для вибору першої з показаних: ").strip()
            selected_ip = user_input if user_input else shown[0]["address"]

    # Перевірка існування
    exists = nb.ipam.ip_addresses.get(address=selected_ip)
    if exists:
        print(f"⚠️ IP {selected_ip} вже існує.")
        return exists.address

    tags_payload = []
    if tags:
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            tag_obj = nb.extras.tags.get(name=tag_name)
            if not tag_obj:
                tag_obj = nb.extras.tags.create(name=tag_name)
            tags_payload.append({"id": tag_obj.id})

    created_ip = nb.ipam.ip_addresses.create(
        address=selected_ip,
        status="active",
        description=description,
        dns_name=dns_name,
        tags=tags_payload
    )
    print(f"✅ Створено IP {created_ip.address}")
    return created_ip.address



# ================= Головне меню =================

def main_menu():


    while True:
        print("\n=== Головне меню ===")
        print("1. Переглянути всі префікси")
        print("2. Створити новий префікс")
        print("3. Додати мережу до префіксу")
        print("4. Додати IP")
        print("0. Вихід")

        choice = input("Оберіть дію: ").strip()

        if choice == "1":
            view_prefixes()
        elif choice == "2":
            prefix_input = input("Введіть префікс: ").strip()
            description = input("Введіть description:\n").strip()
            create_prefix(prefix_input, description=description)
        elif choice == "3":
            prefix_input_for_loopback = input("Введіть префікс в якому буде створено loopback: ").strip()
            description_input = input("Введіть description:\n").strip()
            dns_input = input("Введіть dns: ").strip()
            a=create_ip_in_prefix(
                prefix_input_for_loopback,
                description_input,
                'rt' + dns_input + '.mgmt',
                tags=["router","wh"]
            )
            print(f"Створена ІР {a}")
            ip_part, mask = a.split('/')
            octets = ip_part.split('.')

            # зробимо копію, щоб не плутати послідовність
            swapped = octets.copy()
            swapped[2], swapped[3] = swapped[3], swapped[2]
            new_prefix = '.'.join(swapped)

            # на базі тієї ж перестановки — інша модифікація
            sw_for_prefix = swapped.copy()
            sw_for_prefix[3] = '224'
            new_prefix_for_sw = '.'.join(sw_for_prefix)
            print(new_prefix)
            print(new_prefix_for_sw)
            create_prefix(new_prefix + '/24', description=description_input)
            create_prefix(new_prefix_for_sw + '/27', description=f"{description_input} [vlan773]")
            create_ip_in_prefix(
                new_prefix_for_sw + '/27',
                description_input,
                'sw0' + dns_input,
                tags=["switch", "wh"],
                from_end=True)
            create_ip_in_prefix(
                "172.24.64.0/19" ,
                description_input,
                'rt' + dns_input + '.mgmt',
                tags=[""]
            )
            create_ip_in_prefix(
                "172.24.192.0/19",
                description_input,
                'rt' + dns_input + '.mgmt',
                tags=[""]
            )
        elif choice == "4":
            prefix_input = input("Введіть префікс: ").strip()
            create_ip_in_prefix(prefix_input)
        elif choice == "0":
            print("Вихід...")
            break
        else:
            print("❌ Невірний вибір, спробуйте ще раз.")


# ================= Запуск =================
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n🚪 Завершення роботи...")
    except Exception as e:
        print(f"❌ Виникла помилка: {e}")
