# run_exe.py — .exe로 묶을 때의 진입점. streamlit을 코드로 실행한다.
import os
import sys
import streamlit.web.cli as stcli


def resource_path(rel):
    # PyInstaller로 묶이면 파일이 임시폴더(sys._MEIPASS)에 풀린다. 거기서 app.py를 찾음.
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


if __name__ == "__main__":
    sys.argv = [
        "streamlit", "run", resource_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
