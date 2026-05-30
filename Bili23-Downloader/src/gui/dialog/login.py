from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from qfluentwidgets import (
    BodyLabel, ImageLabel, LineEdit, HyperlinkButton, PushButton
)

from gui.component.widget import IndeterminateProgressPushButton, CidComboBox, SectionLabel
from gui.component.dialog import DialogBase

from util.common.enum import ToastNotificationCategory, QRCodeScanStatus
from util.auth import SMS, Captcha, SMSInfo, QRCode, cookie_manager
from util.common import signal_bus, config
from util.network.request import update_cookies

import sys

class LoginDialog(DialogBase):
    def __init__(self, parent = None):
        super().__init__(parent)

        if sys.platform != "darwin":
            self.enable_close_btn()

        self.init_utils()

        self.init_UI()

    def init_UI(self):
        # 左侧为二维码登录区域
        scan_lab = SectionLabel(self.tr("扫描二维码登录"))

        self.qrcode_img = ImageLabel(self)
        self.qrcode_img.setFixedSize(160, 160)
        
        self.scan_status_lab = BodyLabel(self.tr("使用哔哩哔哩客户端扫码登录"))
        self.scan_status_lab.setMinimumWidth(200)
        self.scan_status_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qrcode_layout = QVBoxLayout()
        qrcode_layout.setSpacing(15)
        qrcode_layout.addWidget(scan_lab, alignment = Qt.AlignmentFlag.AlignHCenter)
        qrcode_layout.addWidget(self.qrcode_img, alignment = Qt.AlignmentFlag.AlignHCenter)
        qrcode_layout.addWidget(self.scan_status_lab, alignment = Qt.AlignmentFlag.AlignHCenter)

        # 右侧为登录方式选择区域
        from qfluentwidgets import SegmentedToolWidget, FluentIcon
        from PySide6.QtWidgets import QStackedWidget

        # 创建分段工具控件
        self.segmented_widget = SegmentedToolWidget(self)
        self.segmented_widget.setFixedWidth(200)

        # 创建堆叠窗口
        self.login_stack = QStackedWidget(self)

        # 短信登录面板
        from PySide6.QtWidgets import QWidget
        sms_widget = QWidget(self)
        sms_layout = QVBoxLayout(sms_widget)

        sms_login_lab = SectionLabel(self.tr("短信登录"))

        self.cid_choice = CidComboBox(self)

        self.tel_box = LineEdit(self)
        self.tel_box.setPlaceholderText(self.tr("请输入手机号"))
        self.tel_box.setClearButtonEnabled(True)

        self.verification_box = LineEdit(self)
        self.verification_box.setPlaceholderText(self.tr("请输入验证码"))
        self.verification_box.setClearButtonEnabled(True)

        self.sms_login_btn = IndeterminateProgressPushButton(self.tr("登录"), self)
        self.sms_login_btn.setFixedWidth(175)

        self.send_verification_btn = HyperlinkButton(self)
        self.send_verification_btn.setText(self.tr("获取验证码"))
        self.send_verification_btn.setMinimumWidth(100)

        sms_top_layout = QHBoxLayout()
        sms_top_layout.addWidget(self.cid_choice)
        sms_top_layout.addWidget(self.tel_box)

        sms_bottom_layout = QHBoxLayout()
        sms_bottom_layout.addWidget(self.verification_box)
        sms_bottom_layout.addWidget(self.send_verification_btn)

        sms_layout.addStretch()
        sms_layout.addWidget(sms_login_lab, alignment = Qt.AlignmentFlag.AlignHCenter)
        sms_layout.addSpacing(10)
        sms_layout.addLayout(sms_top_layout)
        sms_layout.addLayout(sms_bottom_layout)
        sms_layout.addSpacing(15)
        sms_layout.addWidget(self.sms_login_btn, alignment = Qt.AlignmentFlag.AlignHCenter)
        sms_layout.addStretch()

        # Cookie登录面板
        cookie_widget = QWidget(self)
        cookie_layout = QVBoxLayout(cookie_widget)

        cookie_login_lab = SectionLabel(self.tr("Cookie登录"))

        self.cookie_text = QTextEdit(self)
        self.cookie_text.setPlaceholderText(self.tr("请粘贴您的哔哩哔哩Cookie"))
        self.cookie_text.setFixedHeight(100)

        self.cookie_login_btn = IndeterminateProgressPushButton(self.tr("使用Cookie登录"), self)
        self.cookie_login_btn.setFixedWidth(175)

        cookie_layout.addStretch()
        cookie_layout.addWidget(cookie_login_lab, alignment = Qt.AlignmentFlag.AlignHCenter)
        cookie_layout.addSpacing(10)
        cookie_layout.addWidget(self.cookie_text)
        cookie_layout.addSpacing(15)
        cookie_layout.addWidget(self.cookie_login_btn, alignment = Qt.AlignmentFlag.AlignHCenter)
        cookie_layout.addStretch()

        # 添加面板到堆叠窗口
        self.login_stack.addWidget(sms_widget)
        self.login_stack.addWidget(cookie_widget)

        # 添加选项到分段控件
        self.segmented_widget.addItem("sms", FluentIcon.PHONE, lambda: self.login_stack.setCurrentIndex(0))
        self.segmented_widget.addItem("cookie", FluentIcon.CODE, lambda: self.login_stack.setCurrentIndex(1))

        # 默认选择短信登录
        self.segmented_widget.setCurrentItem("sms")

        # 右侧布局
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.segmented_widget, alignment = Qt.AlignmentFlag.AlignHCenter)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.login_stack)


        login_layout = QHBoxLayout()
        login_layout.addSpacing(40)
        login_layout.addLayout(qrcode_layout)
        login_layout.addSpacing(40)
        login_layout.addLayout(right_layout)
        login_layout.addSpacing(40)

        self.viewLayout.addSpacing(40 if sys.platform == "darwin" else 8)
        self.viewLayout.addLayout(login_layout)
        self.viewLayout.addSpacing(40)

        self.widget.setMinimumWidth(700)

        # 隐藏底部的按钮组，允许通过点击遮罩区域来关闭对话框
        self.buttonGroup.hide()
        self.setClosableOnMaskClicked(True)

        self.sms_countdown_timer = QTimer(self)
        self.sms_countdown_timer.setInterval(1000)

        self.connect_signals()

    def connect_signals(self):
        self.send_verification_btn.clicked.connect(self.on_send_verification)
        self.sms_login_btn.clicked.connect(self.on_sms_login)
        self.cookie_login_btn.clicked.connect(self.on_cookie_login)

        self.sms.sms_sent.connect(self.on_verfication_sent)

        self.sms_countdown_timer.timeout.connect(self.on_update_sms_countdown)

    def init_utils(self):
        self.sms = SMS(self)
        self.sms.sms_sent.connect(self.on_verfication_sent)
        self.sms.sms_login_success.connect(self.on_sms_login_success)
        self.sms.error.connect(self.show_error_toast_message)

        self.qrcode = QRCode(self)
        self.qrcode.qrcode_generated.connect(self.on_qrcode_update)
        self.qrcode.update_scan_status.connect(self.on_update_scan_status)

        self.captcha = Captcha()

        # 生成二维码，并开始轮询扫码状态
        self.qrcode.generate()
        self.qrcode.start_polling()

    def on_dialog_close(self):
        signal_bus.login.stop_server.emit()

        self.qrcode.stop_polling()

    def on_send_verification(self):
        # 用户请求发送验证码
        if not self.validate_input(self.tel_box, self.tr("Phone number cannot be empty")):
            return
        
        self.sms.update_cid_tel(
            cid = self.cid_choice.currentData(),
            tel = self.tel_box.text().strip()
        )

        # 进行 Cptcha 验证，成功后发送验证码
        self.captcha.init_geetest()
        
    def on_verfication_sent(self):
        # 验证码发送成功
        self.send_verification_btn.setEnabled(False)

        self.sms_countdown_timer.start()

    def on_sms_login(self):
        if not self.validate_input(self.tel_box, self.tr("Phone number cannot be empty")) or not self.validate_input(self.verification_box, self.tr("Verification code cannot be empty")):
            return
        
        self.sms.update_verification_code(self.verification_box.text().strip())

        self.sms.login()

        self.sms_login_btn.setIndeterminateState(True)

    def on_sms_login_success(self):
        self.login_success(self.tr("短信登录成功"))

        self.sms_login_btn.setIndeterminateState(False)

    def on_qrcode_update(self, pixmap: QPixmap):
        # 更新二维码图片
        self.qrcode_img.setPixmap(pixmap)

    def on_update_scan_status(self, status: int):
        match status:
            case QRCodeScanStatus.WAITING_FOR_SCAN:
                status_text = self.tr("使用哔哩哔哩客户端扫码登录")
            
            case QRCodeScanStatus.WAITING_FOR_CONFIRMATION:
                status_text = self.tr("请在设备上确认登录")

            case QRCodeScanStatus.SUCCESS:
                status_text = self.tr("二维码登录成功")

                self.login_success(status_text)

            case QRCodeScanStatus.EXPIRED:
                status_text = self.tr("二维码已过期")

        self.scan_status_lab.setText(status_text)

    def on_update_sms_countdown(self):
        if SMSInfo.countdown == 1:
            self.sms_countdown_timer.stop()

            self.send_verification_btn.setEnabled(True)
            self.send_verification_btn.setText(self.tr("获取验证码"))
            return

        SMSInfo.countdown -= 1

        self.send_verification_btn.setText(self.tr("重新发送({countdown})").format(countdown = SMSInfo.countdown))
        self.send_verification_btn.setEnabled(False)

    def validate_input(self, target: LineEdit, message: str):
        # 对传入的 widget 进行验证
        if target.text().strip() == "":
            self.show_error_toast_message(message)

            target.setError(True)
            target.setFocus()

            return False
        
        return True
    
    def show_error_toast_message(self, message: str):        
        self.show_top_toast_message(ToastNotificationCategory.ERROR, "", message)

        self.sms_login_btn.setIndeterminateState(False)

    def on_cookie_login(self):
        cookie_str = self.cookie_text.toPlainText().strip()
        if not cookie_str:
            self.show_error_toast_message(self.tr("Cookie不能为空"))
            return

        # 解析cookie字符串
        cookie_dict = {}
        for cookie in cookie_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookie_dict[key] = value

        # 检查必要的cookie值
        required_cookies = ['bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'SESSDATA']
        missing_cookies = []
        for cookie_name in required_cookies:
            if cookie_name not in cookie_dict:
                missing_cookies.append(cookie_name)

        if missing_cookies:
            self.show_error_toast_message(self.tr("缺少必要的Cookie: {}").format(', '.join(missing_cookies)))
            return

        # 设置cookie值到config
        config.set(config.bili_jct, cookie_dict.get('bili_jct', ''))
        config.set(config.DedeUserID, cookie_dict.get('DedeUserID', ''))
        config.set(config.DedeUserID__ckMd5, cookie_dict.get('DedeUserID__ckMd5', ''))
        config.set(config.SESSDATA, cookie_dict.get('SESSDATA', ''))
        config.set(config.is_login, True)

        # 更新网络请求的cookie
        update_cookies()

        # 显示登录成功的提示
        self.login_success(self.tr("Cookie登录成功"))

        self.cookie_login_btn.setIndeterminateState(False)

    def login_success(self, message: str):
        signal_bus.toast.show.emit(ToastNotificationCategory.SUCCESS, "", message)

        # 延迟关闭对话框，确保用户能看到登录成功的提示
        QTimer.singleShot(300, self.yesButton.click)
