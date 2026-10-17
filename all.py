# all.py
"""
Все тест-кейсы YouGile в одном файле с Allure-разметкой.
Фикстуры driver и logged_in берутся из conftest.py (лежит рядом).
"""

import os
import re
import time

import allure
import pytest
from allure_commons.types import AttachmentType
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ================= КОНФИГ =================
YOUGILE_URL = "https://ru.yougile.com"
BOARD_URL = os.getenv(
    "BOARD_URL",
    "https://ru.yougile.com/team/cf91bebf06c1/Пример-проекта",
)
EMAIL = "ajgulnigmatullina710@gmail.com"
PASSWORD = os.getenv("YOUGILE_PASSWORD", "Aa*123456A")
# ==========================================


# ---------- Утилиты Allure ----------
def attach_screenshot(driver, name: str):
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=name,
            attachment_type=AttachmentType.PNG,
        )
    except Exception as e:
        print(f"  -> Не удалось прикрепить скриншот: {e}")


def attach_text(name: str, value: str):
    try:
        allure.attach(value, name=name, attachment_type=AttachmentType.TEXT)
    except Exception:
        pass


def open_board(driver):
    with allure.step(f"Открыть доску: {BOARD_URL}"):
        driver.get(BOARD_URL)
        time.sleep(4)
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='board-column']")
            )
        )
        attach_screenshot(driver, "Доска загружена")


def _set_input_js(driver, el, value):
    """Установить значение input через JS — обход ElementNotInteractable."""
    driver.execute_script("""
        const el = arguments[0];
        const value = arguments[1];
        el.removeAttribute('readonly');
        el.removeAttribute('disabled');
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, '');
        el.dispatchEvent(new Event('input', {bubbles: true}));
        setter.call(el, value);
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    """, el, value)


# =========================================================================
# TC-01: Открытие главной страницы
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Главная страница")
@allure.story("Открытие главной страницы")
@allure.title("TC-01: Открытие главной страницы YouGile")
@allure.severity(allure.severity_level.BLOCKER)
def test_tc_01_open_main_page(driver):
    wait = WebDriverWait(driver, 15)

    with allure.step(f"Открыть {YOUGILE_URL}"):
        driver.get(YOUGILE_URL)

    with allure.step("Проверить, что URL содержит yougile.com"):
        assert "yougile.com" in driver.current_url
        attach_text("URL", driver.current_url)

    with allure.step("Проверить, что заголовок не пустой"):
        assert driver.title
        attach_text("Title", driver.title)

    with allure.step("Найти кнопку «Войти»"):
        login_btn = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//a[contains(text(),'Войти')]")
        ))
        assert login_btn.is_displayed() and login_btn.is_enabled()
        attach_screenshot(driver, "Кнопка «Войти» найдена")


# =========================================================================
# TC-01-login: Успешная авторизация
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Авторизация")
@allure.story("Вход в систему")
@allure.title("TC-01-login: Успешная авторизация с валидными данными")
@allure.severity(allure.severity_level.BLOCKER)
def test_tc_01_login(driver):
    with allure.step("Открыть главную"):
        driver.get(YOUGILE_URL)
        driver.delete_all_cookies()
        driver.get(YOUGILE_URL)
        attach_screenshot(driver, "Главная до входа")

    with allure.step("Клик по «Войти»"):
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//a[contains(., 'Войти')] | //button[contains(., 'Войти')]")
            )
        ).click()

    with allure.step(f"Ввести email {EMAIL}"):
        email = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
            )
        )
        email.clear()
        email.send_keys(EMAIL)

    with allure.step("Ввести пароль"):
        pwd = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "input[type='password']")
            )
        )
        pwd.clear()
        pwd.send_keys(PASSWORD)

    with allure.step("Нажать «Войти»"):
        if "/team/" not in driver.current_url:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[@type='submit'] | //button[contains(., 'Войти')]")
                )
            ).click()

    with allure.step("Ожидаем переход на /team/"):
        WebDriverWait(driver, 60).until(EC.url_contains("/team/"))
        attach_text("URL после входа", driver.current_url)
        attach_screenshot(driver, "Личный кабинет")


# =========================================================================
# TC-TM-01: Создание задачи
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Управление задачами")
@allure.story("Создание задачи")
@allure.title("TC-TM-01: Создание задачи с полным набором параметров")
@allure.severity(allure.severity_level.CRITICAL)
def test_tc_tm_01_create_task(logged_in):
    driver = logged_in
    actions = ActionChains(driver)
    task_name = f"Тестовая задача №1 ({int(time.time())})"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step("Найти колонку «Входящие задачи»"):
        column = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Входящие задачи')]")
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", column
        )

    with allure.step("Нажать «Добавить задачу»"):
        add_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Добавить задачу')]")
            )
        )
        actions.move_to_element(add_btn).click().perform()
        time.sleep(1.5)
        attach_screenshot(driver, "Форма создания")

    with allure.step(f"Ввести название: {task_name}"):
        name_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@type='text'] | //textarea")
            )
        )
        name_input.click()
        name_input.clear()
        name_input.send_keys(task_name)
        attach_text("Название", task_name)

    with allure.step("Создать задачу (Enter)"):
        name_input.send_keys(Keys.RETURN)
        time.sleep(2)
        attach_screenshot(driver, "Задача создана")

    with allure.step(f"Проверить, что задача «{task_name}» появилась на доске"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{task_name}')]")
            )
        )
        attach_screenshot(driver, "Итог: задача на доске")


# =========================================================================
# TC-04: Перемещение задачи
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Управление задачами")
@allure.story("Перемещение задачи")
@allure.title("TC-04: Перемещение задачи «Фильтры по каталогу» в «В работе»")
@allure.severity(allure.severity_level.CRITICAL)
def test_tc_04_move_task(logged_in):
    driver = logged_in
    actions = ActionChains(driver)
    task_name = "Фильтры по каталогу"
    source_column_name = "Входящие задачи"
    target_column_name = "В работе"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step(f"Найти задачу «{task_name}» в колонке «{source_column_name}»"):
        source_column = driver.execute_script("""
            const name = arguments[0].toLowerCase();
            const cols = document.querySelectorAll("[data-testid='board-column']");
            for (const c of cols) {
                if ((c.textContent || '').toLowerCase().includes(name)) return c;
            }
            return null;
        """, source_column_name)
        assert source_column is not None

        task_card = driver.execute_script("""
            const col = arguments[0];
            const name = arguments[1].toLowerCase();
            const sels = [
                "[data-testid='board-task-card']",
                "[data-testid='tw-task-container']",
                "[data-testid='tw-task']"
            ].join(', ');
            for (const c of col.querySelectorAll(sels)) {
                if ((c.textContent || '').toLowerCase().includes(name)) return c;
            }
            return null;
        """, source_column, task_name)
        assert task_card is not None
        attach_screenshot(driver, "Задача найдена")

    with allure.step(f"Найти колонку «{target_column_name}»"):
        target_column = driver.execute_script("""
            const name = arguments[0].toLowerCase();
            const cols = document.querySelectorAll("[data-testid='board-column']");
            for (const c of cols) {
                if ((c.textContent || '').toLowerCase().includes(name)) return c;
            }
            return null;
        """, target_column_name)
        assert target_column is not None

    with allure.step(f"Перетащить «{task_name}» → «{target_column_name}»"):
        actions.move_to_element(task_card).click_and_hold().pause(1) \
               .move_to_element(target_column).pause(1).release().perform()
        time.sleep(3)
        attach_screenshot(driver, "После drag-and-drop")

    with allure.step("Проверить, что задача ушла из исходной колонки"):
        still_in_source = driver.execute_script("""
            const col = arguments[0];
            const name = arguments[1].toLowerCase();
            const sels = [
                "[data-testid='board-task-card']",
                "[data-testid='tw-task-container']",
                "[data-testid='tw-task']"
            ].join(', ');
            for (const c of col.querySelectorAll(sels)) {
                if ((c.textContent || '').toLowerCase().includes(name)) return true;
            }
            return false;
        """, source_column, task_name)
        assert not still_in_source, "Задача всё ещё в исходной колонке"

    with allure.step(f"Проверить, что задача появилась в «{target_column_name}»"):
        in_target = driver.execute_script("""
            const col = arguments[0];
            const name = arguments[1].toLowerCase();
            const sels = [
                "[data-testid='board-task-card']",
                "[data-testid='tw-task-container']",
                "[data-testid='tw-task']"
            ].join(', ');
            for (const c of col.querySelectorAll(sels)) {
                if ((c.textContent || '').toLowerCase().includes(name)) return true;
            }
            return false;
        """, target_column, task_name)
        assert in_target, "Задача не найдена в целевой колонке"


# =========================================================================
# TC-05: Редактирование названия задачи
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Управление задачами")
@allure.story("Редактирование задачи")
@allure.title("TC-05: Редактирование названия задачи")
@allure.severity(allure.severity_level.NORMAL)
def test_tc_05_edit_task_name(logged_in):
    driver = logged_in
    actions = ActionChains(driver)

    base_name = "Просмотр товаров в корзине"
    new_name = f"Просмотр товаров в корзине (ред. {int(time.time())})"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step(f"Найти задачу по подстроке «{base_name}»"):
        card = driver.execute_script("""
            const base = arguments[0].toLowerCase();
            const sels = [
                "[data-testid='board-task-card']",
                "[data-testid='tw-task-container']",
                "[data-testid='tw-task']"
            ].join(', ');
            for (const c of document.querySelectorAll(sels)) {
                if ((c.textContent || '').toLowerCase().includes(base)) return c;
            }
            return null;
        """, base_name)
        assert card is not None, (
            f"Не найдена задача, содержащая «{base_name}»."
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", card
        )
        time.sleep(1)
        attach_screenshot(driver, "Задача найдена")

    with allure.step("Открыть карточку двойным кликом"):
        actions.move_to_element(card).pause(0.3).double_click().perform()
        time.sleep(2)
        attach_screenshot(driver, "Карточка открыта")

    def _dump_inputs():
        print("      [debug] Видимые поля на странице:")
        for sel in ["input", "textarea", "[contenteditable='true']"]:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if not el.is_displayed():
                        continue
                    ph = el.get_attribute("placeholder") or ""
                    tp = el.get_attribute("type") or ""
                    cls = (el.get_attribute("class") or "")[:60]
                    print(f"        <{el.tag_name} type='{tp}' "
                          f"placeholder='{ph}' class='{cls}'>")
                except Exception:
                    continue

    def _find_edit_field():
        for sel in ["//input[@type='text']", "//textarea"]:
            for el in driver.find_elements(By.XPATH, sel):
                try:
                    ph = (el.get_attribute("placeholder") or "").lower()
                    if el.is_displayed() and "поиск" not in ph:
                        return el
                except Exception:
                    continue
        for el in driver.find_elements(
            By.XPATH, "//*[@contenteditable='true']"
        ):
            try:
                if el.is_displayed():
                    return el
            except Exception:
                continue
        return None

    with allure.step(f"Изменить название на «{new_name}»"):
        _dump_inputs()
        text_input = _find_edit_field()

        if text_input is None:
            with allure.step("Кликнуть по названию задачи в карточке"):
                title_candidates = driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{base_name}')]"
                )
                for el in title_candidates:
                    try:
                        if el.is_displayed():
                            actions.move_to_element(el).pause(0.2) \
                                .double_click().perform()
                            time.sleep(1)
                            break
                    except Exception:
                        continue
                text_input = _find_edit_field()

        if text_input is None:
            with allure.step("Нажать кнопку редактирования"):
                edit_btn_candidates = [
                    (By.XPATH, "//button[contains(@aria-label, 'дактир')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'Edit')]"),
                    (By.XPATH, "//*[contains(@data-testid, 'edit')]"),
                    (By.XPATH, "//*[contains(@class, 'edit')]"),
                ]
                for loc in edit_btn_candidates:
                    try:
                        btn = driver.find_element(*loc)
                        if btn.is_displayed():
                            driver.execute_script(
                                "arguments[0].click();", btn
                            )
                            time.sleep(1)
                            text_input = _find_edit_field()
                            if text_input:
                                break
                    except Exception:
                        continue

        assert text_input is not None, (
            "Не найдено поле редактирования названия. "
            "См. скриншот карточки."
        )

        if text_input.get_attribute("contenteditable") == "true":
            driver.execute_script("""
                const el = arguments[0];
                el.focus();
                el.innerHTML = '';
            """, text_input)
            text_input.send_keys(new_name)
        else:
            _set_input_js(driver, text_input, new_name)

        time.sleep(0.5)
        text_input.send_keys(Keys.RETURN)
        time.sleep(2)
        attach_screenshot(driver, "Название изменено")

    with allure.step(f"Проверить, что новое название «{new_name}» на доске"):
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{new_name}')]")
            )
        )


# =========================================================================
# TC-06: Удаление задачи
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Управление задачами")
@allure.story("Удаление задачи")
@allure.title("TC-06: Удаление задачи «Обложка с котиком»")
@allure.severity(allure.severity_level.CRITICAL)
def test_tc_06_delete_task(logged_in):
    driver = logged_in
    actions = ActionChains(driver)
    task_name = "Обложка с котиком"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step(f"Найти задачу «{task_name}»"):
        task_card = driver.execute_script("""
            const name = arguments[0].toLowerCase();
            const cards = document.querySelectorAll(
                "[data-testid='board-task-card'], " +
                "[data-testid='tw-task-container'], " +
                "[data-testid='tw-task']"
            );
            for (const c of cards) {
                if ((c.textContent || '').toLowerCase().includes(name)) return c;
            }
            return null;
        """, task_name)
        assert task_card is not None
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", task_card
        )
        time.sleep(1)
        attach_screenshot(driver, "Задача найдена")

    with allure.step("Навести мышь — появляется «⋮»"):
        actions.move_to_element(task_card).pause(0.5).perform()
        time.sleep(1)

    with allure.step("Открыть меню «⋮»"):
        menu_btn = driver.execute_script("""
            const card = arguments[0];
            let m = card.querySelector("[data-testid='board-task-menu']");
            if (m && m.offsetWidth > 0) return m;
            const icons = card.querySelectorAll(
                ".hint__cnt, [role='button'], div[class*='cursor-pointer']"
            );
            for (const el of icons) {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) return el;
            }
            return null;
        """, task_card)
        assert menu_btn is not None
        driver.execute_script("arguments[0].click();", menu_btn)
        time.sleep(2)
        attach_screenshot(driver, "Меню открыто")

    with allure.step("Нажать «Удалить» в меню"):
        delete_item = driver.execute_script("""
            const items = document.querySelectorAll(
                "[role='menuitem'], div[class*='cursor-pointer'], li, button, a"
            );
            for (const it of items) {
                if ((it.textContent || '').trim() !== 'Удалить') continue;
                const r = it.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                const cx = r.left + r.width / 2;
                const cy = r.top + r.height / 2;
                const top = document.elementFromPoint(cx, cy);
                if (it === top || it.contains(top)) return it;
            }
            return null;
        """)
        assert delete_item is not None
        driver.execute_script("arguments[0].click();", delete_item)
        time.sleep(2)

    with allure.step("Подтвердить в диалоге «Удалить задачу?»"):
        end_time = time.time() + 10
        confirmed = False
        while time.time() < end_time:
            confirm_btn = driver.execute_script("""
                const btns = document.querySelectorAll(
                    "button, [role='button'], div[class*='cursor-pointer']"
                );
                for (const b of btns) {
                    if ((b.textContent || '').trim() !== 'Удалить') continue;
                    const r = b.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const cx = r.left + r.width / 2;
                    const cy = r.top + r.height / 2;
                    const top = document.elementFromPoint(cx, cy);
                    if (b === top || b.contains(top)) return b;
                }
                return null;
            """)
            if confirm_btn is not None:
                attach_screenshot(driver, "Диалог подтверждения")
                driver.execute_script("arguments[0].click();", confirm_btn)
                confirmed = True
                break
            time.sleep(0.5)
        assert confirmed, "Диалог подтверждения не появился"

    with allure.step("Проверить, что задача исчезла с доски"):
        end_time = time.time() + 15
        gone = False
        while time.time() < end_time:
            still_exists = driver.execute_script("""
                const name = arguments[0].toLowerCase();
                const cards = document.querySelectorAll(
                    "[data-testid='board-task-card'], " +
                    "[data-testid='tw-task-container'], " +
                    "[data-testid='tw-task']"
                );
                for (const c of cards) {
                    if ((c.textContent || '').toLowerCase().includes(name)) return true;
                }
                return false;
            """, task_name)
            if not still_exists:
                gone = True
                break
            time.sleep(0.5)
        assert gone, "Задача всё ещё на доске"
        attach_screenshot(driver, "Итог: задача удалена")# =========================================================================
# TC-07: Поиск задачи через глобальный поиск
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Поиск")
@allure.story("Глобальный поиск")
@allure.title("TC-07: Поиск задачи «Авторизация пользователя по номеру т»")
@allure.severity(allure.severity_level.NORMAL)
def test_tc_07_search_task(logged_in):
    driver = logged_in
    query = "Авторизация"
    expected = "Авторизация пользователя по номеру т"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step("Найти поле поиска в шапке"):
        search_input = driver.execute_script("""
            const sels = [
                "div.search-top input[placeholder='Поиск']",
                "div.search-top input[placeholder*='Поиск']",
                "input[placeholder='Поиск']",
            ];
            for (const s of sels) {
                for (const el of document.querySelectorAll(s)) {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const cx = r.left + r.width / 2;
                    const cy = r.top + r.height / 2;
                    const top = document.elementFromPoint(cx, cy);
                    if (el === top || el.contains(top)) return el;
                }
            }
            return null;
        """)
        assert search_input is not None

    with allure.step(f"Ввести запрос «{query}»"):
        driver.execute_script(
            "arguments[0].focus(); arguments[0].click();", search_input
        )
        time.sleep(0.5)
        _set_input_js(driver, search_input, query)
        time.sleep(2)
        attach_screenshot(driver, "Результаты поиска")

    with allure.step(f"Проверить, что найдена задача «{expected}»"):
        found = len(driver.find_elements(
            By.XPATH,
            f"//*[contains(normalize-space(.), '{expected}')]"
        )) > 0
        assert found, "Задача не найдена в результатах"


# =========================================================================
# TC-08: Переключение на диаграмму Ганта
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Виды доски")
@allure.story("Переключение вида")
@allure.title("TC-08: Переключение вида на диаграмму Ганта")
@allure.severity(allure.severity_level.NORMAL)
def test_tc_08_switch_gantt(logged_in):
    driver = logged_in

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step("Активировать вид «Доска»"):
        board_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Доска')]")
            )
        )
        board_btn.click()
        time.sleep(2)

    with allure.step("Переключиться на «Гант»"):
        gantt_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space()='Гант']")
            )
        )
        gantt_btn.click()
        time.sleep(3)
        attach_screenshot(driver, "Вид «Гант»")

    with allure.step("Проверить, что на странице есть даты"):
        body = driver.find_element(By.TAG_NAME, "body").text
        pattern = r"\d{2}[.\-/]\d{2}[.\-/]\d{2,4}"
        assert re.search(pattern, body), \
            "На диаграмме Ганта не найдена шкала времени"

    with allure.step("Вернуться на «Доска»"):
        board_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Доска')]")
            )
        )
        board_btn.click()
        time.sleep(2)
        attach_screenshot(driver, "Возврат на «Доска»")


# =========================================================================
# TC-09: Создание новой доски
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Доски")
@allure.story("Создание доски")
@allure.title("TC-09: Создание новой доски «Тест-доска QA»")
@allure.severity(allure.severity_level.NORMAL)
def test_tc_09_create_board(logged_in):
    driver = logged_in
    board_name = f"Тест-доска QA {int(time.time())}"

    with allure.step("Открыть доску"):
        open_board(driver)

    with allure.step("Открыть меню «+» создания доски"):
        add_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='add-new-board']")
            )
        )
        driver.execute_script("arguments[0].click();", add_btn)
        attach_screenshot(driver, "Меню создания доски")

    with allure.step("Выбрать «Доска с задачами»"):
        item = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Доска с задачами')]")
            )
        )
        item.click()

        # Небольшая пауза, чтобы шапка перестроилась и поле ввода точно появилось в DOM
        time.sleep(1)
        attach_screenshot(driver, "После выбора «Доска с задачами»")

    with allure.step(f"Ввести название «{board_name}»"):
        def _is_board_name_input(d):
            # 1) Ищем по точному плейсхолдеру (input или textarea)
            for el in d.find_elements(
                    By.XPATH,
                    "//input[contains(@placeholder, 'Название доски')]"
                    " | //textarea[contains(@placeholder, 'Название доски')]"
                    " | //input[contains(@placeholder, 'азвание доск')]"
                    " | //textarea[contains(@placeholder, 'азвание доск')]"
            ):
                if el.is_displayed():
                    return el

            # 2) Fallback: ищем любой видимый input или textarea (кроме поиска)
            for el in d.find_elements(By.XPATH, "//input | //textarea"):
                try:
                    ph = (el.get_attribute("placeholder") or "").lower()
                    if not el.is_displayed() or "поиск" in ph:
                        continue
                    # Проверяем, что это не поле глобального поиска в шапке
                    in_search = d.execute_script(
                        "return !!(arguments[0].closest('.search-top, [class*=search]'));", el
                    )
                    if in_search:
                        continue
                    return el
                except Exception:
                    continue
            return False

        # Ждём до 20 секунд появления поля
        name_input = WebDriverWait(driver, 20).until(_is_board_name_input)

        # Кликаем через JS (обходим перекрытия анимацией) и ставим фокус
        driver.execute_script("arguments[0].click(); arguments[0].focus();", name_input)
        time.sleep(0.5)

        # Очищаем и вводим текст
        name_input.clear()
        name_input.send_keys(board_name)
        time.sleep(0.5)

        # Жмём Enter для сохранения
        name_input.send_keys(Keys.RETURN)
        time.sleep(2)
        attach_screenshot(driver, "Новая доска создана")

    with allure.step(f"Проверить, что вкладка «{board_name}» появилась"):
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//*[contains(@data-testid, 'board-tab') and contains(., '{board_name}')] | "
                 f"//*[contains(text(), '{board_name}')]")
            )
        )


# =========================================================================
# TC-10: Переключение видов проекта
# =========================================================================
@allure.epic("YouGile")
@allure.feature("Виды доски")
@allure.story("Переключение видов проекта")
@allure.title("TC-10: Переключение видов Доска → Гант → Календарь → Доска")
@allure.severity(allure.severity_level.MINOR)
def test_tc_10_switch_views(logged_in):
    driver = logged_in

    def _switch_to(view_name):
        with allure.step(f"Переключиться на «{view_name}»"):
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     f"//div[@role='button'][contains(normalize-space(.), '{view_name}')] | "
                     f"//*[normalize-space()='{view_name}']")
                )
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            attach_screenshot(driver, f"Вид «{view_name}»")

    with allure.step("Открыть доску"):
        open_board(driver)

    _switch_to("Доска")
    with allure.step("Проверить, что активен канбан-вид"):
        assert driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Входящие задачи')]"
        ), "Канбан не отображается"

    _switch_to("Гант")
    _switch_to("Календарь")
    _switch_to("Доска")

    with allure.step("Проверить возврат на канбан"):
        assert driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Входящие задачи')]"
        ), "Не вернулись на канбан"


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-v"])