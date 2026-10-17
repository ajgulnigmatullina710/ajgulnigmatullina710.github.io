# conftest.py
"""
Общие фикстуры и утилиты для всех тестов YouGile.
pytest подхватывает этот файл автоматически — импортировать его не нужно.
"""

import os
import time

import allure
import pytest
from allure_commons.types import AttachmentType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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


def attach_html(driver, name: str = "HTML страницы"):
    try:
        allure.attach(
            driver.page_source,
            name=name,
            attachment_type=AttachmentType.HTML,
        )
    except Exception:
        pass


# ---------- Хелперы для ввода ----------
def _find_clickable_input(driver, css_selector, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        for el in driver.find_elements(By.CSS_SELECTOR, css_selector):
            try:
                if not el.is_displayed() or not el.is_enabled():
                    continue
                clickable = driver.execute_script("""
                    const el = arguments[0];
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) return false;
                    const cx = r.left + r.width / 2;
                    const cy = r.top + r.height / 2;
                    const top = document.elementFromPoint(cx, cy);
                    return el === top || el.contains(top);
                """, el)
                if clickable:
                    return el
            except Exception:
                continue
        time.sleep(0.5)
    return None


def _set_input_js(driver, el, value):
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


# ---------- Фикстура: чистый драйвер ----------
@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--lang=ru-RU")
    d = webdriver.Chrome(options=options)
    # ВАЖНО: не используем implicitly_wait — он конфликтует с WebDriverWait.

    yield d

    try:
        attach_screenshot(d, "Скриншот при завершении теста")
        attach_html(d, "HTML при завершении теста")
    except Exception:
        pass
    d.quit()


# ---------- Фикстура: авторизованный драйвер ----------
@pytest.fixture
def logged_in(driver):
    """Авторизует пользователя и возвращает драйвер."""
    with allure.step("Открыть главную страницу YouGile"):
        driver.get(YOUGILE_URL)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    with allure.step("Закрыть баннер cookie, если есть"):
        for loc in [
            (By.XPATH, "//button[contains(., 'Принять')]"),
            (By.XPATH, "//button[contains(., 'Согласен')]"),
            (By.XPATH, "//*[contains(text(), 'Принять все')]"),
        ]:
            closed = False
            for el in driver.find_elements(*loc):
                try:
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        closed = True
                        break
                except Exception:
                    continue
            if closed:
                break

    with allure.step("Открыть форму входа"):
        # Сначала ждём наличие кнопки «Войти» или поля пароля
        WebDriverWait(driver, 30).until(
            lambda d: (
                d.find_elements(By.XPATH, "//a[contains(., 'Войти')]")
                or d.find_elements(By.XPATH, "//button[contains(., 'Войти')]")
                or d.find_elements(By.CSS_SELECTOR, "input[type='password']")
                or d.find_elements(By.CSS_SELECTOR, "input[type='email']")
            )
        )
        has_password_now = bool(
            driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        )
        if not has_password_now:
            clicked = False
            for loc in [
                (By.XPATH, "//a[contains(., 'Войти')]"),
                (By.XPATH, "//button[contains(., 'Войти')]"),
                (By.XPATH, "//*[contains(text(),'Войти')]"),
            ]:
                for el in driver.find_elements(*loc):
                    try:
                        if el.is_displayed() and el.is_enabled():
                            driver.execute_script(
                                "arguments[0].click();", el
                            )
                            clicked = True
                            break
                    except Exception:
                        continue
                if clicked:
                    break
            assert clicked, "Не нашли и не смогли кликнуть по кнопке «Войти»"

        # Ждём появления поля пароля (presence, а не clickable)
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='password']")
            )
        )
        time.sleep(1)
        attach_screenshot(driver, "Форма входа открыта")

    with allure.step(f"Ввести email: {EMAIL}"):
        email_input = _find_clickable_input(
            driver,
            "input[type='email'], input[name='email'], "
            "input[placeholder*='mail' i], input[placeholder*='почт' i]",
            timeout=30,
        )
        if email_input is None:
            for el in driver.find_elements(
                By.CSS_SELECTOR, "input[type='email'], input[name='email']"
            ):
                if el.is_displayed():
                    email_input = el
                    break
        assert email_input is not None, "Не найдено поле Email"
        try:
            email_input.click()
            email_input.clear()
            email_input.send_keys(EMAIL)
            if not (email_input.get_attribute("value") or "").strip():
                raise RuntimeError
        except Exception:
            _set_input_js(driver, email_input, EMAIL)

    with allure.step("Ввести пароль"):
        pass_input = _find_clickable_input(
            driver, "input[type='password']", timeout=15
        )
        if pass_input is None:
            for el in driver.find_elements(
                By.CSS_SELECTOR, "input[type='password']"
            ):
                if el.is_displayed():
                    pass_input = el
                    break
        assert pass_input is not None, "Не найдено поле Пароль"
        try:
            pass_input.click()
            pass_input.clear()
            pass_input.send_keys(PASSWORD)
            if not (pass_input.get_attribute("value") or "").strip():
                raise RuntimeError
        except Exception:
            _set_input_js(driver, pass_input, PASSWORD)
        time.sleep(0.3)

    with allure.step("Нажать кнопку «Войти»"):
        submitted = False
        for loc in [
            (By.CSS_SELECTOR, "form button[type='submit']"),
            (By.CSS_SELECTOR, "form input[type='submit']"),
            (By.XPATH, "//form//button[contains(., 'Войти')]"),
            (By.XPATH, "//button[contains(., 'Войти')]"),
        ]:
            for el in driver.find_elements(*loc):
                try:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].click();", el)
                        submitted = True
                        break
                except Exception:
                    continue
            if submitted:
                break
        if not submitted:
            pass_input.send_keys(Keys.ENTER)

    with allure.step("Дождаться авторизации"):
        WebDriverWait(driver, 60).until(
            lambda d: "/login" not in d.current_url
        )
        WebDriverWait(driver, 30).until(
            lambda d: "/team/" in d.current_url
            or d.find_elements(By.CSS_SELECTOR, "[data-testid='board-column']")
            or d.find_elements(By.CSS_SELECTOR, "[data-testid='add-new-board']")
        )
        time.sleep(2)
        attach_screenshot(driver, "Личный кабинет после входа")

    return driver


# ---------- Хелпер: открыть доску ----------
def open_board(driver):
    with allure.step(f"Открыть доску: {BOARD_URL}"):
        driver.get(BOARD_URL)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='board-column']")
            )
        )
        attach_screenshot(driver, "Доска загружена")