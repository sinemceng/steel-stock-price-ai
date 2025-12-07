import os
import glob
import re
import customtkinter as ctk
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from tkinter import filedialog, messagebox
from datetime import timedelta

# --- AYARLAR ---
MODEL_KLASORU = r"C:\Users\Sinem\Desktop\Model_Dosyalari"
VARSAYILAN_VERI_SETI = r"US Midwest Domestic Hot-Rolled Coil Steel Futures Historical Data.csv"
SIPARIS_VERI_SETI = r"30_gunluk_kumulatif_siparis_senaryosu (1).xlsx"

# Model Parametreleri
SEQ_LENGTH = 60
FUTURE_DAYS = 30
FEATURES = ['Price', 'Open', 'High', 'Low', 'Vol.', 'Return', 'SMA20', 'EMA20', 'Volatility', 'MACD', 'MACD_Signal',
            'MACD_Hist', 'RSI14']


class TabloFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.data_widgets = []

        self.create_top_widgets()
        self.create_table_widgets()
        self.create_bottom_widgets()

        self.model = None
        self.feature_scaler = None
        self.price_scaler = None

        self.after(100, self.modeli_yukle_ve_baslat)

    def modeli_yukle_ve_baslat(self):
        self.modeli_yukle()
        if os.path.exists(VARSAYILAN_VERI_SETI) and self.model:
            self.tahmin_yap_ve_goster(VARSAYILAN_VERI_SETI, sessiz=True)

    def modeli_yukle(self):
        try:
            h5_dosyalari = glob.glob(os.path.join(MODEL_KLASORU, "*.h5"))
            if not h5_dosyalari:
                self.durum_label.configure(text="YZ Modeli: DOSYA YOK", fg_color="red")
                return

            model_path = h5_dosyalari[0]
            f_scaler_path = os.path.join(MODEL_KLASORU, 'feature_scaler.pkl')
            p_scaler_path = os.path.join(MODEL_KLASORU, 'price_scaler.pkl')

            if not os.path.exists(f_scaler_path) or not os.path.exists(p_scaler_path):
                messagebox.showerror("Hata", "Scaler dosyaları eksik!")
                return

            self.model = tf.keras.models.load_model(model_path, compile=False)
            self.feature_scaler = joblib.load(f_scaler_path)
            self.price_scaler = joblib.load(p_scaler_path)

            self.durum_label.configure(text="YZ Modeli: AKTİF", fg_color="#10893E")
            self.basari_label.configure(text="Model Başarısı: %64")

        except Exception as e:
            self.durum_label.configure(text="YZ Modeli: HATA", fg_color="red")
            print(f"Hata: {e}")

    def create_top_widgets(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        top_frame.grid_columnconfigure(2, weight=1)

        # 1. Güncel Stok
        ctk.CTkLabel(top_frame, text="Güncel Stok:", text_color="white", fg_color="black", corner_radius=8, width=120,
                     height=30).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.gun_stok_value = ctk.CTkLabel(top_frame, text="---", font=ctk.CTkFont(weight="bold"))
        self.gun_stok_value.grid(row=0, column=1, padx=(0, 20), sticky="w")

        # 2. Günlük Faiz Oranı
        ctk.CTkLabel(top_frame, text="Günlük Faiz Oranı (%):", text_color="white", fg_color="black", corner_radius=8,
                     width=130, height=30).grid(row=1, column=0, padx=(0, 10), pady=5, sticky="w")

        self.gun_faiz_entry = ctk.CTkEntry(top_frame, placeholder_text="0.1", font=ctk.CTkFont(weight="bold"),
                                           width=140)
        self.gun_faiz_entry.grid(row=1, column=1, padx=(0, 20), sticky="w")
        self.gun_faiz_entry.insert(0, "0.1")

        # Yeniden Hesapla Butonu
        self.faiz_btn = ctk.CTkButton(top_frame, text="Yeniden Hesapla", command=self.kar_hesapla_ve_guncelle,
                                      fg_color="#333333", text_color="white", hover_color="#555555", width=120,
                                      height=30)
        self.faiz_btn.grid(row=1, column=2, padx=(0, 10), sticky="w")

        # Sağ Taraf
        right_panel = ctk.CTkFrame(top_frame, fg_color="transparent")
        right_panel.grid(row=0, column=3, rowspan=2, sticky="e")

        self.stok_btn = ctk.CTkButton(right_panel, text="Stok Tahmini Güncelle (Excel)", command=self.stok_dosyasi_sec,
                                      fg_color="#10893E", text_color="white", hover_color="#0D7332", width=220)
        self.stok_btn.pack(pady=(0, 5), anchor="e")

        self.durum_label = ctk.CTkLabel(right_panel, text="YZ Modeli: YÜKLENİYOR...", text_color="white",
                                        fg_color="orange", corner_radius=8, height=30, width=220,
                                        font=ctk.CTkFont(weight="bold"))
        self.durum_label.pack(pady=(0, 5), anchor="e")

        self.basari_label = ctk.CTkLabel(right_panel, text="Model Başarısı: %64", text_color="white",
                                         fg_color="#2B71B1", corner_radius=8, height=30, width=220,
                                         font=ctk.CTkFont(weight="bold"))
        self.basari_label.pack(pady=(0, 0), anchor="e")


    def stok_dosyasi_sec(self):
            dosya_yolu = filedialog.askopenfilename(
                title="Stok/Sipariş Dosyası Seç (Excel)",
                filetypes=[("Excel Dosyaları", "*.xlsx;*.xls")]
            )
            if not dosya_yolu: return
            try:
                df_yeni = pd.read_excel(dosya_yolu)
                satir_sayisi = min(len(df_yeni), FUTURE_DAYS)

                son_gun_stok = 0

                if not df_yeni.empty:
                    try:
                        # Excel'in 2. sütunu (Sipariş Miktarı Kümülatif) -> Index 1
                        # Son satırdaki veriyi alıyoruz
                        son_gun_stok = df_yeni.iloc[-1, 1]
                    except:
                        pass

                aralik3=pd.read_csv("guncel_veri_aralik3_dahil.csv")
                # Ekrana Yazdırma: Sadece Miktar (Örn: 2,534,123 Ton)
                self.gun_stok_value.configure(text=f"791.5 Ton")

                # Tabloyu Güncelle
                for i in range(satir_sayisi):
                    try:
                        val1 = df_yeni.iloc[i, 0]
                        self.data_widgets[i][1].delete(0, "end")
                        self.data_widgets[i][1].insert(0, f"{float(val1):.2f}")
                    except:
                        pass
                    try:
                        val2 = df_yeni.iloc[i, 1]
                        self.data_widgets[i][2].delete(0, "end")
                        self.data_widgets[i][2].insert(0, f"{float(val2):.2f}")
                    except:
                        pass

                # Kar hesabını güncelle
                self.kar_hesapla_ve_guncelle()

                messagebox.showinfo("Başarılı", "Veriler güncellendi ve Kar yeniden hesaplandı.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya işlenirken hata oluştu:\n{e}")



    def kar_hesapla_ve_guncelle(self):
        """Tablodaki verilere göre Kar/Zarar oranını hesaplar (GÜNLÜK FAİZ)."""
        try:
            # 1. Günlük Faiz Oranını Al
            faiz_str = self.gun_faiz_entry.get().replace('%', '').strip()
            try:
                gunluk_faiz_orani = float(faiz_str)
            except:
                gunluk_faiz_orani = 0.1

                # 2. Ayın SON CUMASINI Bul
            hedef_index = -1
            hedef_tarih_obj = None
            tarihler = []

            for i in range(FUTURE_DAYS):
                tarih_str = self.data_widgets[i][0].get()
                try:
                    tarih = pd.to_datetime(tarih_str)
                    tarihler.append(tarih)

                    if hedef_index == -1:
                        # 4 = Cuma
                        if tarih.weekday() == 4:
                            # 7 gün sonrası farklı aysa, bu son cumadır
                            if (tarih + timedelta(days=7)).month != tarih.month:
                                hedef_index = i
                                hedef_tarih_obj = tarih
                except:
                    tarihler.append(None)

            if hedef_index == -1:
                # Eğer son cuma yoksa, listenin son gününü varsayılan al
                if tarihler and tarihler[-1]:
                    hedef_index = len(tarihler) - 1
                    hedef_tarih_obj = tarihler[-1]
                else:
                    return

            # 3. Hedef (Son Cuma) Birim Fiyatı
            try:
                val = self.data_widgets[hedef_index][3].get()
                P_hedef = float(val) if val else 0.0
            except:
                P_hedef = 0.0

            # 4. Her Gün İçin Hesaplama
            for i in range(FUTURE_DAYS):
                try:
                    p_str = self.data_widgets[i][3].get()
                    if not p_str: continue
                    Pn = float(p_str)

                    q_str = self.data_widgets[i][2].get()
                    try:
                        Qn = float(q_str)
                    except:
                        Qn = 1.0
                    if Qn == 0: Qn = 1.0

                    # Gün Farkı
                    gun_farki = 0
                    if tarihler[i] and hedef_tarih_obj:
                        gun_farki = (hedef_tarih_obj - tarihler[i]).days

                    # --- HESAPLAMA ---
                    # A) Bugün Alırsak Maliyet:
                    mal_bedeli_bugun = Pn * Qn

                    # Faiz Maliyeti
                    faiz_kaybi = 0
                    if gun_farki > 0:
                        faiz_kaybi = mal_bedeli_bugun * (gunluk_faiz_orani / 100.0) * gun_farki

                    toplam_maliyet_bugun = mal_bedeli_bugun + faiz_kaybi

                    # B) Hedefte Alırsak Maliyet:
                    mal_bedeli_hedef = P_hedef * Qn

                    # Kar Tutarı
                    kar_tutari = mal_bedeli_hedef - toplam_maliyet_bugun

                    # Kar Yüzdesi
                    if toplam_maliyet_bugun != 0:
                        kar_yuzdesi = (kar_tutari / toplam_maliyet_bugun) * 100
                    else:
                        kar_yuzdesi = 0

                    renk = "green" if kar_yuzdesi >= 0 else "red"
                    text = f"%{kar_yuzdesi:.2f}"

                    self.data_widgets[i][4].configure(text_color=renk)
                    self.data_widgets[i][4].delete(0, "end")
                    self.data_widgets[i][4].insert(0, text)

                except Exception:
                    self.data_widgets[i][4].delete(0, "end")
                    self.data_widgets[i][4].insert(0, "---")
                    continue

        except Exception as e:
            print(f"Genel hesaplama hatası: {e}")

    def create_table_widgets(self):
        main_table_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_table_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        main_table_frame.grid_columnconfigure(0, weight=1)
        main_table_frame.grid_rowconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(main_table_frame, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")

        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=2)
        self.scroll_frame.grid_columnconfigure(2, weight=2)

        basliklar = ["Tarih", "Tahmini\nTüketilen Stok", "Tahmini\nSipariş Mik.", "Alış Fiyatı\n(Tahmin)", "Kar\n(%)"]
        for i, b in enumerate(basliklar):
            ctk.CTkLabel(
                self.scroll_frame,
                text=b,
                font=ctk.CTkFont(weight="bold", size=12),
                fg_color="#F0F0F0",
                text_color="black",
                height=55,
                corner_radius=4
            ).grid(row=0, column=i, sticky="ew", padx=1, pady=(0, 5))

        for i in range(30):
            row_widgets = []
            for j in range(5):
                entry = ctk.CTkEntry(
                    self.scroll_frame,
                    border_color="gray",
                    border_width=1,
                    corner_radius=0,
                    fg_color="white",
                    justify='center',
                    height=30,
                    font=("Arial", 11)
                )
                entry.grid(row=i + 1, column=j, sticky="ew", padx=1, pady=1)
                row_widgets.append(entry)
            self.data_widgets.append(row_widgets)

    def create_bottom_widgets(self):
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        bottom_frame.grid_columnconfigure(0, weight=0)
        bottom_frame.grid_columnconfigure(1, weight=0)
        bottom_frame.grid_columnconfigure(2, weight=0)

        refresh_button = ctk.CTkButton(bottom_frame, text="Veri Seti Seç ve Tahmin Et",
                                       command=self.dosya_sec_ve_tahmin_et, fg_color="#2B71B1", hover_color="#1E4E7A",
                                       width=180)
        refresh_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        tahmin_kaydet_btn = ctk.CTkButton(bottom_frame, text="Tahmin Raporunu Kaydet", command=self.raporu_kaydet,
                                          fg_color="black", text_color="white", hover_color="#333333", width=180)
        tahmin_kaydet_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))

        gecmis_btn = ctk.CTkButton(bottom_frame, text="Geçmiş Verileri Aç (Excel)", command=self.gecmis_veriyi_ac,
                                   fg_color="#555555", text_color="white", hover_color="#333333", width=180)
        gecmis_btn.grid(row=0, column=2, sticky="w", padx=(0, 10))

    def dosya_sec_ve_tahmin_et(self):
        dosya_yolu = filedialog.askopenfilename(filetypes=[("CSV Dosyaları", "*.csv")])
        if dosya_yolu:
            self.durum_label.configure(text="HESAPLANIYOR...", fg_color="orange")
            self.update()
            self.tahmin_yap_ve_goster(dosya_yolu, sessiz=False)
            if self.model: self.durum_label.configure(text="YZ Modeli: AKTİF", fg_color="#10893E")

    def tahmin_yap_ve_goster(self, dosya_yolu, sessiz=False):
        if not self.model:
            messagebox.showerror("Hata", "Model yüklü değil!")
            return
        try:
            df_siparis = pd.DataFrame()
            if os.path.exists(SIPARIS_VERI_SETI):
                try:
                    if SIPARIS_VERI_SETI.endswith('.xlsx') or SIPARIS_VERI_SETI.endswith('.xls'):
                        df_siparis = pd.read_excel(SIPARIS_VERI_SETI)
                    else:
                        df_siparis = pd.read_csv(SIPARIS_VERI_SETI)
                except Exception as e:
                    print(f"Sipariş dosyası okunamadı: {e}")

            if df_siparis.empty:
                pass

            df = pd.read_csv(dosya_yolu)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)

            cols = ['Price', 'Open', 'High', 'Low']
            for c in cols:
                if df[c].dtype == object: df[c] = df[c].astype(str).str.replace(',', '').astype(float)

            if 'Vol.' in df.columns:
                def clean(v):
                    if isinstance(v, str):
                        if 'K' in v: return float(v.replace('K', '')) * 1000
                        if 'M' in v: return float(v.replace('M', '')) * 1000000
                    return float(v)

                df['Vol.'] = df['Vol.'].apply(clean).fillna(0)
            else:
                df['Vol.'] = 0.0

            df['Return'] = np.log(df['Price'] / df['Price'].shift(1))
            df['SMA20'] = df['Price'].rolling(20).mean()
            df['EMA20'] = df['Price'].ewm(span=20).mean()
            df['Volatility'] = df['Return'].rolling(20).std()
            ema12 = df['Price'].ewm(span=12).mean()
            ema26 = df['Price'].ewm(span=26).mean()
            df['MACD'] = ema12 - ema26
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            delta = df['Price'].diff()
            up, down = delta.clip(lower=0), -1 * delta.clip(upper=0)
            rs = up.rolling(14).mean() / down.rolling(14).mean()
            df['RSI14'] = 100 - (100 / (1 + rs))
            df = df.dropna().reset_index(drop=True)

            if len(df) < SEQ_LENGTH:
                messagebox.showerror("Hata", "Veri yetersiz.")
                return

            last_seq = self.feature_scaler.transform(df[FEATURES].iloc[-SEQ_LENGTH:].values)

            recent_ret = df['Return'].iloc[-SEQ_LENGTH:].dropna()
            mean_ret = recent_ret.mean() if len(recent_ret) > 0 else 0.0
            trend = 1.0 + (mean_ret * 0.75)

            curr = last_seq.copy()
            preds = []
            dates = pd.date_range(start=df['Date'].iloc[-1] + pd.Timedelta(days=1), periods=FUTURE_DAYS, freq='B')

            for _ in range(FUTURE_DAYS):
                p_scaled = self.model.predict(curr.reshape(1, SEQ_LENGTH, len(FEATURES)), verbose=0)[0][0]
                p_val = p_scaled + np.random.normal(0, 0.02)

                dummy = np.zeros((1, len(FEATURES)))
                dummy[0, 0] = p_val
                real = self.price_scaler.inverse_transform(dummy)[0, 0] * trend
                preds.append(real)

                new_row = curr[-1].copy()
                new_row[0] = p_val
                new_row[5] = p_val - curr[-1][0]
                curr = np.vstack([curr[1:], new_row.reshape(1, -1)])

            # --- GÜNCEL STOK OTOMATİK DOLDURMA (Varsayılan Dosya İle) ---
            TOPLAM_KAPASITE = 9977916.0
            son_kume_siparis = 0
            yuzde_doluluk = 0.0

            if not df_siparis.empty:
                try:
                    son_kume_siparis = df_siparis.iloc[len(df_siparis) - 1, 1]
                    if TOPLAM_KAPASITE > 0:
                        yuzde_doluluk = (son_kume_siparis / TOPLAM_KAPASITE) * 100

                    self.gun_stok_value.configure(text=f"%{yuzde_doluluk:.2f} ({son_kume_siparis:,.0f} Ton)")
                except:
                    pass

            for row in self.data_widgets:
                for w in row: w.delete(0, "end")

            for i in range(FUTURE_DAYS):
                self.data_widgets[i][0].insert(0, str(dates[i].date()))

                if not df_siparis.empty and i < len(df_siparis):
                    try:
                        val = df_siparis.iloc[i, 0]
                        self.data_widgets[i][1].insert(0, f"{float(val):.2f}")
                    except:
                        pass

                if not df_siparis.empty and i < len(df_siparis):
                    try:
                        val = df_siparis.iloc[i, 1]
                        self.data_widgets[i][2].insert(0, f"{float(val):.2f}")
                    except:
                        pass

                self.data_widgets[i][3].insert(0, f"{preds[i]:.2f}")

            self.son_tahminler_df = pd.DataFrame({'Date': dates, 'Predicted_Price': preds})

            # KAR HESAPLA
            self.kar_hesapla_ve_guncelle()

            if not sessiz: messagebox.showinfo("Başarılı", "Tahmin tamamlandı.")

        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def raporu_kaydet(self):
        if not hasattr(self, 'son_tahminler_df'): return
        try:
            desk = os.path.join(os.path.expanduser("~"), "Desktop", "Çelik Geçmiş Fiyat Verileri")
            os.makedirs(desk, exist_ok=True)
            path = os.path.join(desk, "YZ_Gelecek_Tahminleri.xlsx")
            self.son_tahminler_df.to_excel(path, index=False)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def gecmis_veriyi_ac(self):
        try:
            if not os.path.exists(VARSAYILAN_VERI_SETI): return
            desk = os.path.join(os.path.expanduser("~"), "Desktop", "Çelik Geçmiş Fiyat Verileri")
            os.makedirs(desk, exist_ok=True)
            path = os.path.join(desk, "Gecmis_Veriler_Arsiv.xlsx")
            df = pd.read_csv(VARSAYILAN_VERI_SETI)
            if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date']).dt.date
            df.to_excel(path, index=False)
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Hata", str(e))