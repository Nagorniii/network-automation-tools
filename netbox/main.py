from pynetbox import api
from dotenv import load_dotenv
from ipaddress import ip_network, ip_address
from tabulate import tabulate
import os, math

# ====== Підключення до NetBox ======
load_dotenv()
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
nb = api(NETBOX_URL, token=NETBOX_TOKEN)


# ================= Функції =================
def view_prefixes(filter_str=None, per_page=10):
    prefixes = nb.ipam.prefixes.all()
    if not prefixes:
        print("Префіксів немає.")
        return []

    # === ФІЛЬТР ===
    if not filter_str:
        filter_str = input("Введіть частину адреси або опису для фільтрації (або Enter для всіх): ").strip()

    filtered = [
        p for p in prefixes
        if filter_str.lower() in p.prefix.lower() or filter_str.lower() in (p.description or "").lower()
    ]

    if not filtered:
        print("Нічого не знайдено.")
        return []

    # === ПАГІНАЦІЯ ===
    total = len(filtered)
    total_pages = math.ceil(total / per_page)
    page = 1

    while True:
        start = (page - 1) * per_page
        end = start + per_page
        page_data = filtered[start:end]

        table = [[p.prefix, p.status.value, p.description or "—"] for p in page_data]
        print("\n" + tabulate(table, headers=["Prefix", "Status", "Description"], tablefmt="fancy_grid"))
        print(f"📄 Сторінка {page}/{total_pages} | Всього записів: {total}")

        # === НАВІГАЦІЯ ===
        if total_pages == 1:
            break

        action = input("\n[n] Наступна | [p] Попередня | [q] Вихід: ").strip().lower()
        if action == "n" and page < total_pages:
            page += 1
        elif action == "p" and page > 1:
            page -= 1
        elif action == "q" or action == "":
            break
        else:
            print("⚠️ Невірна команда.")

def validate_prefix(prefix_str: str):
    try:
        return str(ip_network(prefix_str, strict=False))
    except ValueError:
        print("❌ Невірний формат префіксу.")
        return None


def create_prefix(prefix, description="Створено скриптом"):
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


def create_ip_in_prefix(prefix_str, description="", dns_name="", tags=None, ip_address=None, from_end=False):
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


def create_multiple_ips_in_prefix(
        prefix_str: str,
        count: int = 1,
        description: str = "",
        dns_template: str | None = None,
        dns_list: list | None = None,
        tags: list | None = None,
        start_ip: str | None = None,
        from_end: bool = False
):
    # Перевірка префіксу
    prefix = nb.ipam.prefixes.get(prefix=prefix_str)
    if not prefix:
        print(f"❌ Префікс {prefix_str} не знайдено.")
        return []

    # Отримуємо список вільних IP (список словників з 'address')
    available = prefix.available_ips.list()  # це список dict з ключем 'address'
    available_addresses = [a['address'].split('/')[0] for a in available]  # тільки IP без /mask

    if not available_addresses and not start_ip:
        print(f"⚠️ Вільних IP немає у {prefix_str}.")
        return []

    # Підготуємо dns-імена
    if dns_list:
        if len(dns_list) != count:
            print("❌ Довжина dns_list не збігається з count.")
            return []
        dns_names = dns_list
    elif dns_template:
        dns_names = [dns_template.format(n=i + 1) for i in range(count)]
    else:
        dns_names = ["" for _ in range(count)]

    # Підготовка тегів
    tags_payload = []
    if tags:
        for tn in (t for t in tags if t and t.strip()):
            tag_obj = nb.extras.tags.get(name=tn.strip()) or nb.extras.tags.create(name=tn.strip())
            tags_payload.append({"id": tag_obj.id})

    # Визначаємо початкові IP для створення
    selected_ips = []

    if start_ip:
        # Переконаємось, що start_ip є валідним і є в available -> потім інкрементуємо
        base_ip = start_ip.split('/')[0]
        mask = ""
        if start_ip and '/' in start_ip:
            mask = '/' + start_ip.split('/')[1]
        try:
            cur = ip_address(base_ip)
        except ValueError:
            print("❌ Некоректний start_ip.")
            return []

        if base_ip in available_addresses:
            idx = available_addresses.index(base_ip)

            for i in range(count):
                if idx + i < len(available_addresses):
                    selected_ips.append(available_addresses[idx + i])
                else:

                    candidate = str(ip_address(base_ip) + i)
                    selected_ips.append(candidate)
        else:

            for i in range(count):
                selected_ips.append(str(cur + i))

    else:
        # Вибираємо по first/last available
        if from_end:
            pool = list(reversed(available_addresses))
        else:
            pool = available_addresses

        if len(pool) < count:
            print(f"⚠️ В префіксі лише {len(pool)} вільних IP, запитано {count}. Буде створено {len(pool)}.")
        for i in range(min(count, len(pool))):
            selected_ips.append(pool[i])

    # Створюємо IP-адреси у NetBox по черзі
    created = []
    for idx, ip in enumerate(selected_ips):
        dns = dns_names[idx] if idx < len(dns_names) else ""
        exists = nb.ipam.ip_addresses.get(address=ip)
        if exists:
            print(f"⚠️ IP {ip} вже існує — пропускаємо.")
            created.append(exists.address)
            continue

        try:
            obj = nb.ipam.ip_addresses.create(
                address=f"{ip}{mask}",
                status="active",
                description=description,
                dns_name=dns,
                tags=tags_payload
            )
            print(f"✅ Створено IP {obj.address} (dns: {dns})")
            created.append(obj.address)
        except Exception as e:
            print(f"❌ Помилка при створенні {ip}: {e}")

    return created


# ================= Головне меню =================

def main_menu():
    while True:
        print("\n=== Головне меню ===")
        print("1. Переглянути всі префікси")
        print("2. Створити новий префікс")
        print("3. Додати мережу до префіксу")
        print("4. Додати IP")
        print("5. Створити декілька ІР")
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
            a = create_ip_in_prefix(
                prefix_input_for_loopback,
                description_input,
                'rt' + dns_input + '.mgmt',
                tags=["router", "wh"]
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
                "172.24.64.0/19",
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
        elif choice == "5":
            prefix_input = input("Введіть префікс в якому необхідно створити ІР: ").strip()
            count = int(input("Скільки ІР необхідно додати? "))
            dns_template = input("Приклад DNS: sw{n}.wh ")
            description_input = input("Введіть description: ").strip()
            start_ip = input("Початкова ІР: ")
            tags_input = input("Введіть теги через пробіл: ").strip()

            tags_list = [t.strip() for t in tags_input.split() if t.strip()]
            create_multiple_ips_in_prefix(
                prefix_str=prefix_input,
                count=count,
                start_ip=start_ip,
                dns_template=dns_template,
                description=description_input,
                tags=tags_list
            )

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
        print("\n Завершення роботи...")
    except Exception as e:
        print(f"❌ Виникла помилка: {e}")
