# mitmx.timeweb

Ansible-коллекция для интеграции с **Timeweb Cloud** через динамический 
inventory-плагин `mitmx.timeweb.timeweb`.

---

##  Описание

Коллекция предоставляет inventory-плагин, который получает список 
серверов из API Timeweb Cloud и динамически формирует инвентарь для Ansible.

---

##  Подробности коллекции

| Поле             | Описание                                             |
|------------------|------------------------------------------------------|
| **Collection** | `mitmx.timeweb`                                        |
| **Inventory Plugin** | `mitmx.timeweb.timeweb`                          |
| **Supported API Endpoint** | `https://api.timeweb.cloud/api/v1/servers` |
| **Requirements** | Python `requests`, действующий API-токен Timeweb     |


---

##  Установка

### Из приватного Git-репозитория (HTTPS):

```yaml
# requirements.yml
collections:
  - name: https://github.com/mitmx/timeweb-ansible-collection.git
    type: git
    version: main
```

Установка:

```bash
ansible-galaxy collection install -r requirements.yml
```

Или напрямую:

```bash
ansible-galaxy collection install git+https://github.com/mitmx/timeweb-ansible-collection.git
```

---

## Использование

Создайте inventory-файл, например `timeweb.yml`:

```yaml
plugin: mitmx.timeweb.timeweb
api_token: "{{ lookup('env','TIMEWEB_TOKEN') }}"
validate_certs: true

# Необязательные параметры:
# compose:
#   ansible_user: "'root'"
# keyed_groups:
#   - key: region
#     prefix: region_
# groups:
#   running: "'status' in hostvars[inventory_hostname] and hostvars[inventory_hostname]['status'] == 'on'"
```

Проверка работы:

```bash
ansible-inventory -i timeweb.yml --list
```

Запуск плейбука с этим inventory:

```bash
ansible-playbook -i timeweb.yml site.yml
```

---

## Получение API-токена

1. Зайдите в свой аккаунт Timeweb Cloud → раздел **API токены**.
2. Создайте токен с правами на чтение серверов.
3. Установите его в переменную окружения:

```bash
export TIMEWEB_TOKEN="ваш_api_токен"
```

---

## Параметры плагина

| Параметр         | Обязателен | Значение по умолчанию       | Описание                                   |
| ---------------- | ---------- | --------------------------- |--------------------------------------------|
| `plugin`         | Да         | —                           | Должен быть `mitmx.timeweb.timeweb`        |
| `api_token`      | Да         | —                           | API-токен Timeweb Cloud                    |
| `api_endpoint`   | Нет        | `https://api.timeweb.cloud` | Базовый URL API                            |
| `validate_certs` | Нет        | `true`                      | Проверять SSL-сертификаты                  |
| `compose`        | Нет        | `{}`                        | Определение переменных через Jinja2        |
| `keyed_groups`   | Нет        | `[]`                        | Автосоздание групп по значениям переменных |
| `groups`         | Нет        | `{}`                        | Создание групп по условиям                 |

---

## Пример вывода

Результат `ansible-inventory --list`:

```json
{
  "_meta": {
    "hostvars": {
      "some-server-name-here": {
        "ansible_host": "1.2.3.4",
        "id": 1234567,
        "status": "off",
        "flavor": null,
        "region": "ru-1",
        "tags": [],
        "project": 123
      },
      "another-server-name-here": {
        "ansible_host": "1.2.3.5",
        "id": 1234568,
        "status": "on",
        "flavor": null,
        "region": "ru-3",
        "tags": [],
        "project": 123
      }
    }
  },
  "all": {
    "children": ["ungrouped"]
  }
}
```
