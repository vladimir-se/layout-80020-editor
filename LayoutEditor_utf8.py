# coding: UTF-8


import time
import sys
import os
import datetime
import lxml.etree as et
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
# GUI
from gui import Ui_MainWindow
# resources
import res


class LEMainWindow(QtWidgets.QMainWindow):
    '''
    Основной класс
    '''
    def __init__(self):
        super(LEMainWindow, self).__init__()
        # Некоммерческие присоединения
        self.non_profit_measuringpoints = []
        #  Состояние макета (редактировался?)
        self.edited_by_template = False
        #
        self.ui = Ui_MainWindow()
        self.setup_ui()


    def setup_ui(self):
        '''
        Инициализация элементов графического интерфейса.
        Установка значений по умолчанию.
        '''
        self.ui.setupUi(self)
        # Строка меню
        self.init_menu()
        # treeView
        self.template_data_model = QtGui.QStandardItemModel()
        self.template_data_model_reference = QtGui.QStandardItemModel()
        # self.template_data_model.setColumnCount(9)
        self.header_labels = ['Точка учета', 'Начало', 'Окончание', 'Статус', 'A+', 'A-', 'R+', 'R-', '']
        self.template_data_model.setHorizontalHeaderLabels(self.header_labels)
        self.ui.templateDataTree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.templateDataTree.setAlternatingRowColors(True)
        self.ui.templateDataTree.setAllColumnsShowFocus(True)
        self.ui.templateDataTree.setMinimumWidth(640)
        self.ui.templateDataTree.setMinimumHeight(480)
        self.ui.templateDataTree.setModel(self.template_data_model)
        self.ui.templateDataTree.selectionModel().selectionChanged.connect(self.treeview_select_row)
        # Название вкладок
        self.ui.tabWidget.setTabText(self.ui.tabWidget.indexOf(self.ui.tab_1), 'Статус')
        self.ui.tabWidget.setTabText(self.ui.tabWidget.indexOf(self.ui.tab_2), 'Объём')
        self.ui.tabWidget.setTabText(self.ui.tabWidget.indexOf(self.ui.tab_3), 'Направление')
        # Общая область
        self.ui.label_selected_measuringpoint.setText('Присоединение')
        # Комбобокс с присоединениями
        self.ui.comboBox_selected_measuringpoint.setStyleSheet('combobox-popup: 0;')
        self.ui.comboBox_selected_measuringpoint.currentTextChanged.connect(self.treeview_select_row_in_combobox)
        # Комбобоксы выбора интервала
        self.ui.startTime_label.setText('Начало:')
        self.ui.startPeriod_comboBox.setStyleSheet('combobox-popup: 0;')
        self.ui.endTime_label.setText('Окончание:')
        self.ui.endPeriod_comboBox.setStyleSheet('combobox-popup: 0;')
        # Вкладка 'Статус'
        # Выбор типа присоединения
        self.ui.measuringpointType_label.setText('Присоединения:')
        self.ui.comboBox_measuringpoint_type.addItems(('', 'Все'))
        # Инициализация интервалов
        self.populate_period()
        # Реинициализация времемени окончания после выбора времени начала
        self.ui.startPeriod_comboBox.currentIndexChanged.connect(lambda: self.populate_period(
            start_time=self.ui.startPeriod_comboBox.currentText()))
        # Комбобокс выбора флага
        self.ui.selectFlag_label.setText('Флаг:')
        self.ui.comboBox_select_flag.addItems(('0', '1'))
        # Вкладка 'Объем'
        # Инициализация чекбоксов по каналам
        self.ui.checkBox_save_a_plus.setText('Только получасовка')
        self.ui.checkBox_save_a_plus.setChecked(True)
        self.ui.checkBox_save_a_minus.setText('Только получасовка')
        self.ui.checkBox_save_a_minus.setChecked(True)
        self.ui.checkBox_save_r_plus.setText('Только получасовка')
        self.ui.checkBox_save_r_plus.setChecked(True)
        self.ui.checkBox_save_r_minus.setText('Только получасовка')
        self.ui.checkBox_save_r_minus.setChecked(True)
        #
        self.ui.label_a_plus.setText('Активная приём (A+)')
        self.ui.label_a_minus.setText('Активная отдача (A-)')
        self.ui.label_r_plus.setText('Реактивная приём (R+)')
        self.ui.label_r_minus.setText('Реактивная отдача (R-)')
        # Валидация полей
        input_validator = QtGui.QRegExpValidator(QtCore.QRegExp('^\d\d{0,5}$'))
        self.ui.lineEdit_a_plus.setValidator(input_validator)
        self.ui.lineEdit_a_minus.setValidator(input_validator)
        self.ui.lineEdit_r_plus.setValidator(input_validator)
        self.ui.lineEdit_r_minus.setValidator(input_validator)
        # Вкладкаа 'Направление'
        self.ui.pushButton_A_change.setText('(A+) ↔ (A-)')
        self.ui.pushButton_R_change.setText('(R+) ↔ (R-)')
        self.ui.pushButton_A_change.clicked.connect(lambda: self.change_direction(channel = 'A'))
        self.ui.pushButton_R_change.clicked.connect(lambda: self.change_direction(channel = 'R'))
        # По умолчанию кнопки не активны
        self.ui.pushButton_A_change.setEnabled(False)
        self.ui.pushButton_R_change.setEnabled(False)
        # Кнопка применить
        self.ui.pushButton_apply.setText('Применить')
        # По умолчанию кнопка не активна
        self.ui.pushButton_apply.setEnabled(False)
        self.ui.pushButton_apply.clicked.connect(self.clicked_pushbutton_apply)


    def init_menu(self):
        '''
        Инициализация строки меню.
        Наполнение пунктов меню, привязка действий к функциям, задание параметров по умолчанию.
        '''
        # Меню "Файл"
        filemenu = self.ui.menubar.addMenu('Файл')
        self.open_xml_action = QtWidgets.QAction('Открыть макет', self)
        self.open_xml_action.triggered.connect(self.open_xml)
        filemenu.addAction(self.open_xml_action)

        self.save_xml_action = QtWidgets.QAction('Сохранить макет', self)
        self.save_xml_action.triggered.connect(self.save_xml)
        filemenu.addAction(self.save_xml_action)
        self.save_xml_action.setEnabled(False)

        self.exit_action = QtWidgets.QAction('Выход', self)
        self.exit_action.triggered.connect(QtWidgets.qApp.quit)
        filemenu.addAction(self.exit_action)

        about = self.ui.menubar.addMenu('?')
        self.about_action = QtWidgets.QAction('О программе', self)
        self.about_action.triggered.connect(lambda: QtWidgets.QMessageBox.about(self, "О программе", "<h4 align=center>Программа для правки макета 80020<br><a href='https://github.com/nuxster/ASKUE'>Сайт программы</a></h4>"))
        about.addAction(self.about_action)


    def treeview_select_row_in_combobox(self):
        '''
        Действия при выборе присоединения в combobox'e присоединениями.
        '''
        try:
            self.ui.templateDataTree.selectionModel().select(
                self.template_data_model.indexFromItem(self.template_data_model.findItems(
                    self.ui.comboBox_selected_measuringpoint.currentText(), column = 0)[0]),
                QtCore.QItemSelectionModel.ClearAndSelect)
        # При открытии нового макета с уже загруженными данными возникает IndexError (**BUG**)
        except IndexError:
            pass


    def treeview_select_row(self):
        '''
        Действия при выборе строки в treeview.
        '''
        self.ui.comboBox_measuringpoint_type.setCurrentIndex(0)
        indexes = self.ui.templateDataTree.selectedIndexes()
        measuringpoint = indexes[0].parent().data(QtCore.Qt.DisplayRole) or indexes[0].data(QtCore.Qt.DisplayRole)
        self.populate_comboBox_selected_measuringpoint(current_item=measuringpoint)
        try:
            # Установка интервала в combobox'ах в соответствии с выбором в treeview
            self.populate_period(start_time=indexes[1].data(QtCore.Qt.DisplayRole))
            # Вывод объемов на редактирование по каналам
            self.ui.lineEdit_a_plus.setText(indexes[4].data(QtCore.Qt.DisplayRole))
            self.ui.lineEdit_a_minus.setText(indexes[5].data(QtCore.Qt.DisplayRole))
            self.ui.lineEdit_r_plus.setText(indexes[6].data(QtCore.Qt.DisplayRole))
            self.ui.lineEdit_r_minus.setText(indexes[7].data(QtCore.Qt.DisplayRole))
        except (IndexError, AttributeError):
            pass


    def make_period(self, start_time='0:00'):
        '''
        Создание итераторов периодов.
        '''
        # Преобразование стартового значения для генерации значений периода окончания
        start_time = int(datetime.timedelta(hours=int(start_time.split(':')[0]), minutes=int(start_time.split(':')[1])).seconds/60)
        # Формирования начального и конечного значения получасовки
        start_time_iterator = ((datetime.datetime.min + datetime.timedelta(minutes=i, days=0)).time().strftime('%H:%M') for i in range(start_time, 1441, 30))
        end_time_iterator = ((datetime.datetime.min + datetime.timedelta(minutes=i, days=0)).time().strftime('%H:%M') for i in range(start_time + 30, 1441, 30))
        return((start_time_iterator, end_time_iterator))


    def populate_period(self, start_time='00:00'):
        '''
        Инициализация combobox'ов с выбором интервалов.
        Генерирует наполнение в зависимости от выбора начального значения.
        Контролирует корректность выбранного периода.
        '''
        start, end = self.make_period(start_time)
        # Стартовые значений заполняются только при запуске программы
        if (start_time == '00:00'):
            self.ui.startPeriod_comboBox.addItems(start)
        # Применяется при выборе периода в treeview
        self.ui.startPeriod_comboBox.setCurrentIndex(self.ui.startPeriod_comboBox.findText(start_time))
        self.ui.endPeriod_comboBox.clear()
        self.ui.endPeriod_comboBox.addItems(end)


    def populate_comboBox_selected_measuringpoint(self, current_item=0, measuringpoints=0):
        '''
        Заполнение combobox'а присоединениями из текущего макета.
        '''
        if measuringpoints:
            self.ui.comboBox_selected_measuringpoint.clear()
            self.ui.comboBox_selected_measuringpoint.addItems(measuringpoints)
        else:
            self.ui.comboBox_selected_measuringpoint.setCurrentIndex(self.ui.comboBox_selected_measuringpoint.findText(current_item))


    def open_xml(self):
        '''
        Метод открытия шаблона для обработки.
        '''
        if self.template_data_model.rowCount() > 0:
            self.send_message('Сохрани макет', 1)
            # Очистка основной и эталонной моделей
            self.template_data_model.clear()
            self.template_data_model_reference.clear()
        self.templateXMLfile, _ = QtWidgets.QFileDialog().getOpenFileName(self, 
            'Открыть макет', os.path.dirname(os.path.realpath(__file__)), 'Макет XML (*xml)')
        if os.path.exists(self.templateXMLfile):
            self.tree = et.parse(self.templateXMLfile)
            self.xml_to_treeview()
            # Сохранение эталонной модели для отображения изменений
            for i in range(self.template_data_model.rowCount()):
                measurepoint = QtGui.QStandardItem(self.template_data_model.index(i, 0).data(QtCore.Qt.DisplayRole))
                self.template_data_model_reference.appendRow(measurepoint)
                for row in range(48):
                    _row = []
                    for column in range(8):
                        _row.append(QtGui.QStandardItem(self.template_data_model.index(row, column, self.template_data_model.index(i, 0)).data(QtCore.Qt.DisplayRole)))
                    measurepoint.appendRow(_row)
            # Имя файла-шаблона в сообщении строки состояния
            self.ui.statusbar.showMessage(f'Макет: {self.templateXMLfile.split(os.sep)[-1:][0]}')


    def highlight_changes(self):
        '''
        Процедура подсвечивает измененные (отличные от эталонной модели) 
        данные в TreeView
        '''
        for i in range(self.template_data_model_reference.rowCount()):
            for row in range(48):
                for column in range(1, 8):
                    if not (self.template_data_model_reference.index(row, column, self.template_data_model_reference.index(i, 0)).data(QtCore.Qt.DisplayRole) ==
                        self.template_data_model.index(row, column, self.template_data_model.index(i, 0)).data(QtCore.Qt.DisplayRole)):
                        self.template_data_model.itemFromIndex(self.template_data_model.index(i, 0)).setBackground(QtGui.QColor('#BB94A9'))
                        self.template_data_model.itemFromIndex(self.template_data_model.index(row, column, self.template_data_model.index(i, 0))).setBackground(QtGui.QColor('#BB94A9'))


    def save_xml(self):
        '''
        Сохранение исправленного шаблона.
        '''
        # Синхронизация изменений модели с xmltree
        for child in self.tree.getroot().iterfind('.//'):
            if child.tag == 'area':
                for subchild in child:
                    # Точка учета
                    if subchild.tag == 'measuringpoint':
                        for measuringpoint_count in range(self.template_data_model_reference.rowCount()):
                            # Проход по каждой точке учета
                            if subchild.attrib['name'] == self.template_data_model.index(measuringpoint_count, 0).data(QtCore.Qt.DisplayRole):
                                # Проход по получасовкам
                                for measuringchannel in subchild:
                                    for period in measuringchannel:
                                        for row in range(48):
                                            # КОСЯК ТУТ
                                            if period.attrib['start'] == ''.join(self.template_data_model.index(row, 1, self.template_data_model.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole).split(':')):
                                                for value in period:
                                                    cur = self.template_data_model.index(row, 3, self.template_data_model.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole)
                                                    ref = self.template_data_model_reference.index(row, 3, self.template_data_model_reference.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole)
                                                    if cur != ref:
                                                        value.attrib['status'] = str(cur)
                                                    # value.attrib['status'] = str(self.template_data_model.index(row, 3, self.template_data_model.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole))
                                                    if self.template_data_model.index(row, 3 + int(measuringchannel.attrib['code']), self.template_data_model.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole) != '-':
                                                        value.text = self.template_data_model.index(row, 3 + int(measuringchannel.attrib['code']), self.template_data_model.index(measuringpoint_count, 0)).data(QtCore.Qt.DisplayRole)
        # Сохранение через fileDialog       
        savefile, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Сохранить макет', self.templateXMLfile, 'Макет XML (*xml)')
        try:
            self.tree.write(savefile, encoding='windows-1251')
        except Exception as exception_event:
            self.message('Ошибка записи макета: {0}'.format(exception_event))


    def xml_to_treeview(self):

        '''
        Заполнение модели данных для treeview
        '''
        # Проверка типа макета
        if (self.tree.getroot().tag == 'message') and (self.tree.getroot().attrib['class'] == '80020'):
            pass
        else:
            self.send_message('Макет не соответствует типу!')
            return()
        # Процедура заполнения дерева
        self.template_data_model.clear()
        self.template_data_model.setHorizontalHeaderLabels(self.header_labels)
        # Временный список для некоммерческих присоединений
        non_profit_measuringpoints_list = []
        measuringpoint_list = []
        for child in self.tree.getroot().iterfind('.//'):                
            if child.tag == 'area':
                for subchild in child:
                    # Точка учета
                    if subchild.tag == 'measuringpoint':
                        measuringpoint = QtGui.QStandardItem(subchild.attrib['name'])
                        measuringpoint_list.append(subchild.attrib['name'])
                        measuringpoint.insertColumn(0, [QtGui.QStandardItem(''),])
                        measuringpoint.insertColumn(1, [QtGui.QStandardItem(i) for i in self.make_period()[0]][:-1])
                        measuringpoint.insertColumn(2, [QtGui.QStandardItem(i) for i in self.make_period()[1]])
                        [measuringpoint.insertColumn(i, [QtGui.QStandardItem('-') for i in range(49)]) for i in range(3, 8)]
                        self.template_data_model.appendRow(measuringpoint)
                        # Канал
                        for measuringchannel_in in subchild:
                            # Списки для формирования колонок
                            flag = []
                            measuringchannel_volume = []
                            # Период, флаг, объем
                            for period_in in measuringchannel_in:
                                for value_in in period_in:
                                    # Флаги
                                    try:
                                        # Подсвечивается точка учета и период со статусом == 1
                                        if value_in.attrib['status'] == '1':
                                            _flag = QtGui.QStandardItem(QtGui.QStandardItem(value_in.attrib['status']))
                                            _flag.setBackground(QtGui.QColor('#F4AA90'))
                                            flag.append(_flag)
                                            measuringpoint.setBackground(QtGui.QColor('#F4AA90'))
                                            non_profit_measuringpoints_list.append(measuringpoint.text())
                                    except KeyError:
                                        _flag = QtGui.QStandardItem('0')
                                        flag.append(_flag)
                                    # Объемы
                                    measuringchannel_volume.append(QtGui.QStandardItem(value_in.text))
                            measuringpoint.removeColumn(3 + int(measuringchannel_in.attrib['code']))
                            measuringpoint.insertColumn(3 + int(measuringchannel_in.attrib['code']), measuringchannel_volume)
                        measuringpoint.removeColumn(3)
                        measuringpoint.insertColumn(3, flag)
        # Заполнение combobox'а присоединениями из текущего макета 
        self.populate_comboBox_selected_measuringpoint(measuringpoints=measuringpoint_list)
        # Удаление лишнего из списка некоммерческих присоединений
        self.non_profit_measuringpoints = set(non_profit_measuringpoints_list)
        # Изменение размера столбца с присоединениями по содержимому
        self.ui.templateDataTree.resizeColumnToContents(0)
        # Активировать пункт меню сохраняющий макет
        self.save_xml_action.setEnabled(True)
        # Активировать кнопки
        self.ui.pushButton_apply.setEnabled(True)
        self.ui.pushButton_A_change.setEnabled(True)
        self.ui.pushButton_R_change.setEnabled(True)

    
    def change_status(self, parent_index, flag, start = '0000', end = '0000'):
        '''
        Функция меняет флаг в указанном интервале для каждого измерительного канала.
        '''
        processing_interval = False
        for row in range(48):
            # Начало временного интеравала
            if ':'.join((start[:-2],start[-2:])) == self.template_data_model.index(row, 1, parent_index).data(QtCore.Qt.DisplayRole):
                processing_interval = True
            # Обработка временного интервала
            if processing_interval:
                # Меняем значение флага
                self.template_data_model.setData(self.template_data_model.index(row, 3, parent_index), flag)
                # Вызываем сигнал dataChanged для обновления значений в treeView
                self.template_data_model.dataChanged.emit(self.template_data_model.index(row, 3, parent_index), 
                    self.template_data_model.index(row, 3, parent_index), ())
            # Окончание временного интервала
            if ':'.join((end[:-2],end[-2:])) == self.template_data_model.index(row, 2, parent_index).data(QtCore.Qt.DisplayRole):
                return parent_index


    def adjustment_volume(self, parent_index, measuringchannels_value, start, end):
        '''
        Правка значений на вкладке объем.
        '''
        processing_interval = False
        for row in range(48):
            column = 3
            # Начало временного интеравала
            if ':'.join((start[:-2],start[-2:])) == self.template_data_model.index(row, 1, parent_index).data(QtCore.Qt.DisplayRole):
                processing_interval = True
            # Обработка временного интервала
            if processing_interval:
                for measuringchannel in measuringchannels_value.values():
                    column += 1
                    if measuringchannel[1]:
                        try:
                            self.template_data_model.setData(self.template_data_model.index(row, column, parent_index), str(int(measuringchannel[0])))
                        except ValueError:
                            self.template_data_model.setData(self.template_data_model.index(row, column, parent_index), str(0))
                        # Вызываем сигнал dataChanged для обновления значений в treeView
                        self.template_data_model.dataChanged.emit(self.template_data_model.index(row, column, parent_index), 
                            self.template_data_model.index(row, column, parent_index), ())
            # Окончание временного интервала
            if ':'.join((end[:-2],end[-2:])) == self.template_data_model.index(row, 2, parent_index).data(QtCore.Qt.DisplayRole):
                processing_interval = False


    def change_direction(self, channel):
        '''
        Изменение направления измерений (поменять местами данные на каналах + и -)
        '''
        start = ''.join(self.ui.startPeriod_comboBox.currentText().split(':'))
        end = ''.join(self.ui.endPeriod_comboBox.currentText().split(':'))
        parent_index = self.template_data_model.indexFromItem(self.template_data_model.findItems(self.ui.comboBox_selected_measuringpoint.currentText(), column = 0)[0])
        # Выбор направления
        column = 4 if channel == 'A' else 6
        processing_interval = False
        for row in range(48):
            # Начало временного интеравала
            if ':'.join((start[:-2],start[-2:])) == self.template_data_model.index(row, 1, parent_index).data(QtCore.Qt.DisplayRole):
                processing_interval = True
            # Обработка временного интервала
            if processing_interval:
                plus = int(self.template_data_model.index(row, column, parent_index).data(QtCore.Qt.DisplayRole))
                minus = int(self.template_data_model.index(row, column+1, parent_index).data(QtCore.Qt.DisplayRole))
                # Суммирование не полных получасовок
                if minus != 0 and plus != 0:
                    plus += minus
                    minus = 0
                self.template_data_model.setData(self.template_data_model.index(row, column, parent_index), str(minus))
                self.template_data_model.setData(self.template_data_model.index(row, column+1, parent_index), str(plus))
                # Вызываем сигнал dataChanged для обновления значений в treeView
                self.template_data_model.dataChanged.emit(self.template_data_model.index(row, column, parent_index), 
                    self.template_data_model.index(row, column, parent_index), ())
            # Окончание временного интервала
            if ':'.join((end[:-2],end[-2:])) == self.template_data_model.index(row, 2, parent_index).data(QtCore.Qt.DisplayRole):
                processing_interval = False
        self.highlight_changes()


    def clicked_pushbutton_apply(self):
        '''
        Действия по нажатию кнопки "Применить".
        '''
        if self.template_data_model.rowCount() < 1:
            self.send_message('Требуется загрузить макет.')
            return() # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        start = ''.join(self.ui.startPeriod_comboBox.currentText().split(':'))
        end = ''.join(self.ui.endPeriod_comboBox.currentText().split(':'))
        flag = int(self.ui.comboBox_select_flag.currentText())
        # parent_index = self.ui.templateDataTree.selectedIndexes()[0].parent() or self.ui.templateDataTree.selectedIndexes()[0]
        parent_index = self.template_data_model.indexFromItem(self.template_data_model.findItems(self.ui.comboBox_selected_measuringpoint.currentText(), column = 0)[0])
        # Действия для вкладки "Статус"
        if self.ui.tabWidget.currentIndex() == 0:
            # Если присоединение было выбрано вручную 
            if self.ui.comboBox_measuringpoint_type.currentIndex() == 0:
                self.change_status(parent_index, flag, start, end)
            # Для всего шаблона
            elif self.ui.comboBox_measuringpoint_type.currentIndex() == 1:
                for parent_row in range(self.template_data_model.rowCount()):
                    self.change_status(self.template_data_model.index(parent_row, 0), flag, start, end)
        # Действия для вкладки "Объем"
        elif self.ui.tabWidget.currentIndex() == 1:
            measuringchannels_value = {
                '01':(self.ui.lineEdit_a_plus.text(), self.ui.checkBox_save_a_plus.isChecked()),
                '02':(self.ui.lineEdit_a_minus.text(), self.ui.checkBox_save_a_minus.isChecked()),
                '03':(self.ui.lineEdit_r_plus.text(), self.ui.checkBox_save_r_plus.isChecked()),
                '04':(self.ui.lineEdit_r_minus.text(), self.ui.checkBox_save_r_minus.isChecked())
            }
            self.adjustment_volume(parent_index, measuringchannels_value, start, end)
        # Действия для вкладки "Направление"
        elif self.ui.tabWidget.currentIndex() == 2:
            pass
        # Подсветка измененных данных
        self.highlight_changes()


    def send_message(self, msg, save=0):
        '''
        Вывод сообщений и диалогов.
        '''
        massage_box = QtWidgets.QMessageBox()
        if save == 1:
            btn = massage_box.question(self, 'Сообщение', msg, QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
        else:
            btn = massage_box.question(self, 'Сообщение', msg, QtWidgets.QMessageBox.Ok)
        if btn == QtWidgets.QMessageBox.Yes:
            self.save_xml()
        else:
            pass


def main():
    '''
    Создание экземпляра окна приложения и его запуск.
    '''
    app = QApplication(sys.argv)
    window = LEMainWindow()
    window.setWindowTitle('Редактор макетов')
    window.setWindowIcon(QtGui.QIcon(':/img/LE_ico.png'))
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
