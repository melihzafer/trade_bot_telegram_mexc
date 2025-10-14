"""
Railway CLI Helper - Terminal'den Railway komutları çalıştır
Usage: python railway_cli.py
"""
import subprocess
import sys
import os

class RailwayHelper:
    """Railway CLI yardımcı sınıfı"""
    
    @staticmethod
    def run_command(command):
        """Railway komutunu çalıştır"""
        try:
            result = subprocess.run(
                f"railway {command}",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1
    
    @staticmethod
    def check_installed():
        """Railway CLI kurulu mu kontrol et"""
        stdout, _stderr, code = RailwayHelper.run_command("--version")
        if code == 0:
            print(f"✅ Railway CLI kurulu: {stdout.strip()}")
            return True
        else:
            print("❌ Railway CLI kurulu değil!")
            print("\n📦 Kurulum için:")
            print("npm install -g @railway/cli")
            return False
    
    @staticmethod
    def login():
        """Railway'e login ol"""
        print("🔐 Railway'e login olunuyor...")
        _stdout, stderr, code = RailwayHelper.run_command("login")
        if code == 0:
            print("✅ Login başarılı!")
        else:
            print(f"❌ Login başarısız: {stderr}")
    
    @staticmethod
    def list_projects():
        """Projeleri listele"""
        print("\n📋 Railway Projeleri:")
        stdout, stderr, code = RailwayHelper.run_command("list")
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Hata: {stderr}")
    
    @staticmethod
    def link_project(project_name=None):
        """Projeye bağlan"""
        if project_name:
            print(f"🔗 {project_name} projesine bağlanılıyor...")
            _stdout, stderr, code = RailwayHelper.run_command(f"link {project_name}")
        else:
            print("🔗 Projeye bağlanılıyor...")
            _stdout, stderr, code = RailwayHelper.run_command("link")
        
        if code == 0:
            print("✅ Proje bağlandı!")
        else:
            print(f"❌ Bağlantı başarısız: {stderr}")
    
    @staticmethod
    def show_logs(service=None, lines=50):
        """Logları göster"""
        print(f"\n📜 Son {lines} log satırı:")
        if service:
            cmd = f"logs --service {service} --tail {lines}"
        else:
            cmd = f"logs --tail {lines}"
        
        stdout, stderr, code = RailwayHelper.run_command(cmd)
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Hata: {stderr}")
    
    @staticmethod
    def show_variables():
        """Environment variables göster"""
        print("\n🔐 Environment Variables:")
        stdout, stderr, code = RailwayHelper.run_command("variables")
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Hata: {stderr}")
    
    @staticmethod
    def run_command_on_railway(command):
        """Railway'de komut çalıştır"""
        print(f"\n🚀 Railway'de çalıştırılıyor: {command}")
        stdout, stderr, code = RailwayHelper.run_command(f'run "{command}"')
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Hata: {stderr}")
        return stdout
    
    @staticmethod
    def check_signals_file():
        """signals_raw.jsonl dosyasını kontrol et"""
        print("\n📊 Railway'deki signals_raw.jsonl kontrolü:")
        
        # Dosya var mı?
        _stdout = RailwayHelper.run_command_on_railway("ls -lah data/signals_raw.jsonl")
        
        # Kaç satır var?
        _stdout = RailwayHelper.run_command_on_railway("wc -l data/signals_raw.jsonl")
        
        # Son 5 satır
        print("\n🔥 Son 5 sinyal:")
        _stdout = RailwayHelper.run_command_on_railway("tail -5 data/signals_raw.jsonl")
    
    @staticmethod
    def download_signals():
        """Sinyalleri Railway'den indir"""
        print("\n📥 Sinyaller indiriliyor...")
        
        # Python komutuyla indir
        cmd = """python -c "import sys; sys.stdout.buffer.write(open('data/signals_raw.jsonl', 'rb').read())" """
        _stdout, stderr, code = RailwayHelper.run_command(f'run {cmd}> signals_downloaded.jsonl')
        
        if code == 0 and os.path.exists('signals_downloaded.jsonl'):
            size = os.path.getsize('signals_downloaded.jsonl')
            print(f"✅ İndirildi: signals_downloaded.jsonl ({size} bytes)")
        else:
            print(f"❌ İndirme başarısız: {stderr}")
    
    @staticmethod
    def restart_service(service_name):
        """Servisi yeniden başlat"""
        print(f"\n🔄 {service_name} servisi yeniden başlatılıyor...")
        _stdout, stderr, code = RailwayHelper.run_command(f"restart {service_name}")
        if code == 0:
            print("✅ Servis yeniden başlatıldı!")
        else:
            print(f"❌ Hata: {stderr}")


def main():
    """Ana menü"""
    helper = RailwayHelper()
    
    print("=" * 60)
    print("🚂 RAILWAY CLI HELPER")
    print("=" * 60)
    
    # Railway CLI kurulu mu?
    if not helper.check_installed():
        return
    
    while True:
        print("\n" + "=" * 60)
        print("📋 MENÜ:")
        print("1. Login")
        print("2. Projeleri Listele")
        print("3. Projeye Bağlan")
        print("4. Logları Göster")
        print("5. Environment Variables Göster")
        print("6. signals_raw.jsonl Kontrol Et")
        print("7. Sinyalleri İndir")
        print("8. Servisi Yeniden Başlat")
        print("9. Custom Komut Çalıştır")
        print("0. Çıkış")
        print("=" * 60)
        
        choice = input("\n👉 Seçiminiz: ").strip()
        
        if choice == "1":
            helper.login()
        
        elif choice == "2":
            helper.list_projects()
        
        elif choice == "3":
            project = input("Proje adı (boş bırakırsan menü açılır): ").strip()
            helper.link_project(project if project else None)
        
        elif choice == "4":
            service = input("Service adı (collector/web, boş=hepsi): ").strip()
            lines = input("Kaç satır? (default=50): ").strip()
            lines = int(lines) if lines else 50
            helper.show_logs(service if service else None, lines)
        
        elif choice == "5":
            helper.show_variables()
        
        elif choice == "6":
            helper.check_signals_file()
        
        elif choice == "7":
            helper.download_signals()
        
        elif choice == "8":
            service = input("Service adı (collector/web): ").strip()
            if service:
                helper.restart_service(service)
        
        elif choice == "9":
            cmd = input("Komut girin: ").strip()
            if cmd:
                helper.run_command_on_railway(cmd)
        
        elif choice == "0":
            print("\n👋 Çıkılıyor...")
            break
        
        else:
            print("❌ Geçersiz seçim!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Çıkılıyor...")
        sys.exit(0)