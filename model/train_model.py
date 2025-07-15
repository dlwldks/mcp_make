import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# 📥 데이터 불러오기
df = pd.read_csv("전처리_완료.csv")

# 🎯 타겟 생성: 침수건수 > 0 → 침수 발생(1), 없으면 0
df["침수여부"] = df["침수건수"].apply(lambda x: 1 if x > 0 else 0)

# 🎯 입력 특성 & 타겟 설정
X = df[["강수량_서울", "강수량_부산", "강수량_북부산"]]
y = df["침수여부"]

# 🔀 학습/검증 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 🧠 모델 학습
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# 📊 성능 평가
y_pred = clf.predict(X_test)
print("✅ 분류 결과 평가:")
print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

# 💾 모델 저장
joblib.dump(clf, "flood_classifier_model.pkl")
print("✅ 모델 저장 완료: flood_classifier_model.pkl")
