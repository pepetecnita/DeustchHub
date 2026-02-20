# german_numbers_app.py
# Aplicación de práctica de números en alemán
# Compatible con Pydroid 3 y Kivy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
import random

# Intentar importar TTS (puede no estar disponible en todas las plataformas)
try:
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, cast
    ANDROID = True
except ImportError:
    ANDROID = False
    print("Ejecutando en modo de prueba (sin Android)")

class NumberConverter:
    """Convierte números a palabras en alemán"""
    
    @staticmethod
    def to_german(num):
        """Convierte un número (0-999) a palabras en alemán"""
        ones = ['', 'eins', 'zwei', 'drei', 'vier', 'fünf', 
                'sechs', 'sieben', 'acht', 'neun']
        teens = ['zehn', 'elf', 'zwölf', 'dreizehn', 'vierzehn', 
                 'fünfzehn', 'sechzehn', 'siebzehn', 'achtzehn', 'neunzehn']
        tens = ['', '', 'zwanzig', 'dreißig', 'vierzig', 'fünfzig',
                'sechzig', 'siebzig', 'achtzig', 'neunzig']
        
        if num == 0:
            return 'null'
        if num == 1:
            return 'eins'
        
        result = ''
        
        # Centenas
        if num >= 100:
            hundred_digit = num // 100
            if hundred_digit == 1:
                result += 'einhundert'
            else:
                result += ones[hundred_digit] + 'hundert'
            num %= 100
        
        # Decenas y unidades
        if num >= 20:
            ones_digit = num % 10
            tens_digit = num // 10
            if ones_digit > 0:
                ones_word = 'ein' if ones_digit == 1 else ones[ones_digit]
                result += ones_word + 'und' + tens[tens_digit]
            else:
                result += tens[tens_digit]
        elif num >= 10:
            result += teens[num - 10]
        elif num > 0:
            result += ones[num]
        
        return result
    
    @staticmethod
    def normalize(text):
        """Normaliza texto alemán para comparación"""
        return (text.lower()
                .replace(' ', '')
                .replace('ß', 'ss')
                .replace('ä', 'ae')
                .replace('ö', 'oe')
                .replace('ü', 'ue')
                .strip())


class TextToSpeech:
    """Maneja la síntesis de voz"""
    
    def __init__(self):
        self.tts = None
        if ANDROID:
            self._init_android_tts()
    
    def _init_android_tts(self):
        """Inicializa TTS en Android"""
        try:
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Locale = autoclass('java.util.Locale')
            
            self.tts = TextToSpeech(
                PythonActivity.mActivity,
                None
            )
            self.tts.setLanguage(Locale.GERMAN)
        except Exception as e:
            print(f"Error inicializando TTS: {e}")
    
    def speak(self, text):
        """Pronuncia el texto en alemán"""
        if ANDROID and self.tts:
            try:
                self.tts.speak(text, 0, None, None)
            except Exception as e:
                print(f"Error al hablar: {e}")
        else:
            print(f"[TTS] Pronunciando: {text}")


class ListenModeScreen(Screen):
    """Pantalla del modo Escucha"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_number = 0
        self.tts = TextToSpeech()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Título
        title = Label(
            text='[b]🎧 Modo Escucha[/b]',
            markup=True,
            size_hint=(1, 0.15),
            font_size='24sp'
        )
        
        # Instrucción
        instruction = Label(
            text='Escucha el número y escríbelo en cifras',
            size_hint=(1, 0.1),
            font_size='16sp'
        )
        
        # Botón reproducir
        self.play_btn = Button(
            text='▶️ Reproducir Número',
            size_hint=(1, 0.15),
            background_color=(0.4, 0.4, 1, 1),
            font_size='18sp',
            bold=True
        )
        self.play_btn.bind(on_press=self.play_number)
        
        # Campo de entrada
        self.input_field = TextInput(
            hint_text='Escribe el número aquí...',
            multiline=False,
            size_hint=(1, 0.12),
            font_size='20sp',
            input_type='number'
        )
        
        # Botón verificar
        self.check_btn = Button(
            text='Verificar Respuesta',
            size_hint=(1, 0.12),
            background_color=(0, 0.7, 0, 1),
            font_size='18sp',
            bold=True
        )
        self.check_btn.bind(on_press=self.check_answer)
        
        # Feedback
        self.feedback_label = Label(
            text='',
            size_hint=(1, 0.15),
            font_size='18sp',
            markup=True
        )
        
        # Botón siguiente
        self.next_btn = Button(
            text='↻ Siguiente Número',
            size_hint=(1, 0.12),
            background_color=(0.3, 0.3, 0.8, 1),
            disabled=True
        )
        self.next_btn.bind(on_press=self.next_number)
        
        layout.add_widget(title)
        layout.add_widget(instruction)
        layout.add_widget(self.play_btn)
        layout.add_widget(self.input_field)
        layout.add_widget(self.check_btn)
        layout.add_widget(self.feedback_label)
        layout.add_widget(self.next_btn)
        
        self.add_widget(layout)
        
        # Generar primer número
        self.generate_number()
    
    def generate_number(self):
        """Genera un número aleatorio"""
        self.current_number = random.randint(0, 999)
        self.input_field.text = ''
        self.feedback_label.text = ''
        self.next_btn.disabled = True
        self.check_btn.disabled = False
        self.input_field.disabled = False
    
    def play_number(self, instance):
        """Reproduce el número en alemán"""
        german_text = NumberConverter.to_german(self.current_number)
        self.tts.speak(german_text)
        print(f"Número: {self.current_number} = {german_text}")
    
    def check_answer(self, instance):
        """Verifica la respuesta del usuario"""
        user_answer = self.input_field.text.strip()
        
        if not user_answer:
            self.feedback_label.text = '[color=ff0000]Por favor escribe una respuesta[/color]'
            return
        
        try:
            user_num = int(user_answer)
            if user_num == self.current_number:
                self.feedback_label.text = '[color=00ff00][b]✓ ¡Correcto![/b][/color]'
                app = App.get_running_app()
                app.correct_answers += 1
            else:
                self.feedback_label.text = (
                    f'[color=ff0000][b]✗ Incorrecto[/b][/color]\n'
                    f'Respuesta correcta: {self.current_number}'
                )
        except ValueError:
            self.feedback_label.text = '[color=ff0000]Por favor escribe solo números[/color]'
            return
        
        app = App.get_running_app()
        app.total_answers += 1
        app.update_score()
        
        self.next_btn.disabled = False
        self.check_btn.disabled = True
        self.input_field.disabled = True
    
    def next_number(self, instance):
        """Genera el siguiente número"""
        self.generate_number()


class SpeakModeScreen(Screen):
    """Pantalla del modo Pronunciación"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_number = 0
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Título
        title = Label(
            text='[b]🗣️ Modo Pronunciación[/b]',
            markup=True,
            size_hint=(1, 0.12),
            font_size='24sp'
        )
        
        # Instrucción
        instruction = Label(
            text='Pronuncia el número en alemán',
            size_hint=(1, 0.08),
            font_size='16sp'
        )
        
        # Número mostrado
        self.number_label = Label(
            text='0',
            size_hint=(1, 0.25),
            font_size='72sp',
            bold=True,
            color=(0.3, 0.3, 0.8, 1)
        )
        
        # Campo de entrada (para escribir manualmente)
        self.input_field = TextInput(
            hint_text='Escribe el número en alemán...',
            multiline=False,
            size_hint=(1, 0.12),
            font_size='18sp'
        )
        
        # Botón verificar
        self.check_btn = Button(
            text='Verificar Respuesta',
            size_hint=(1, 0.12),
            background_color=(0, 0.7, 0, 1),
            font_size='18sp',
            bold=True
        )
        self.check_btn.bind(on_press=self.check_answer)
        
        # Feedback
        self.feedback_label = Label(
            text='',
            size_hint=(1, 0.15),
            font_size='16sp',
            markup=True
        )
        
        # Botón siguiente
        self.next_btn = Button(
            text='↻ Siguiente Número',
            size_hint=(1, 0.12),
            background_color=(0.3, 0.3, 0.8, 1),
            disabled=True
        )
        self.next_btn.bind(on_press=self.next_number)
        
        layout.add_widget(title)
        layout.add_widget(instruction)
        layout.add_widget(self.number_label)
        layout.add_widget(Label(
            text='💡 Escribe el número en alemán:',
            size_hint=(1, 0.08),
            font_size='14sp'
        ))
        layout.add_widget(self.input_field)
        layout.add_widget(self.check_btn)
        layout.add_widget(self.feedback_label)
        layout.add_widget(self.next_btn)
        
        self.add_widget(layout)
        
        # Generar primer número
        self.generate_number()
    
    def generate_number(self):
        """Genera un número aleatorio"""
        self.current_number = random.randint(0, 999)
        self.number_label.text = str(self.current_number)
        self.input_field.text = ''
        self.feedback_label.text = ''
        self.next_btn.disabled = True
        self.check_btn.disabled = False
        self.input_field.disabled = False
    
    def check_answer(self, instance):
        """Verifica la respuesta del usuario"""
        user_answer = self.input_field.text.strip()
        
        if not user_answer:
            self.feedback_label.text = '[color=ff0000]Por favor escribe una respuesta[/color]'
            return
        
        correct_answer = NumberConverter.to_german(self.current_number)
        normalized_user = NumberConverter.normalize(user_answer)
        normalized_correct = NumberConverter.normalize(correct_answer)
        
        is_correct = normalized_user == normalized_correct
        
        if is_correct:
            self.feedback_label.text = '[color=00ff00][b]✓ ¡Correcto![/b][/color]'
            app = App.get_running_app()
            app.correct_answers += 1
        else:
            self.feedback_label.text = (
                f'[color=ff0000][b]✗ Incorrecto[/b][/color]\n'
                f'Respuesta correcta: {correct_answer}'
            )
        
        app = App.get_running_app()
        app.total_answers += 1
        app.update_score()
        
        self.next_btn.disabled = False
        self.check_btn.disabled = True
        self.input_field.disabled = True
    
    def next_number(self, instance):
        """Genera el siguiente número"""
        self.generate_number()


class GermanNumbersApp(App):
    """Aplicación principal"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.correct_answers = 0
        self.total_answers = 0
    
    def build(self):
        """Construye la interfaz principal"""
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # Layout principal
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Barra superior con título y puntuación
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        
        title = Label(
            text='[b]🇩🇪 Números en Alemán[/b]',
            markup=True,
            font_size='20sp',
            size_hint=(0.6, 1)
        )
        
        self.score_label = Label(
            text='0 / 0',
            font_size='24sp',
            bold=True,
            size_hint=(0.4, 1),
            color=(0.3, 0.3, 0.8, 1)
        )
        
        top_bar.add_widget(title)
        top_bar.add_widget(self.score_label)
        
        # Botones de modo
        mode_buttons = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        
        self.listen_toggle = ToggleButton(
            text='🎧 Modo Escucha',
            group='mode',
            state='down',
            font_size='16sp'
        )
        self.listen_toggle.bind(on_press=self.switch_to_listen)
        
        self.speak_toggle = ToggleButton(
            text='🗣️ Modo Pronunciación',
            group='mode',
            font_size='16sp'
        )
        self.speak_toggle.bind(on_press=self.switch_to_speak)
        
        mode_buttons.add_widget(self.listen_toggle)
        mode_buttons.add_widget(self.speak_toggle)
        
        # Screen manager para cambiar entre modos
        self.sm = ScreenManager()
        self.listen_screen = ListenModeScreen(name='listen')
        self.speak_screen = SpeakModeScreen(name='speak')
        self.sm.add_widget(self.listen_screen)
        self.sm.add_widget(self.speak_screen)
        
        # Agregar todo al layout principal
        main_layout.add_widget(top_bar)
        main_layout.add_widget(mode_buttons)
        main_layout.add_widget(self.sm)
        
        return main_layout
    
    def switch_to_listen(self, instance):
        """Cambia al modo escucha"""
        self.sm.current = 'listen'
    
    def switch_to_speak(self, instance):
        """Cambia al modo pronunciación"""
        self.sm.current = 'speak'
    
    def update_score(self):
        """Actualiza la puntuación"""
        self.score_label.text = f'{self.correct_answers} / {self.total_answers}'


if __name__ == '__main__':
    GermanNumbersApp().run()
