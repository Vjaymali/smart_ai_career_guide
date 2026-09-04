from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import mysql.connector
from mysql.connector import Error
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from google import genai

# ================= LOAD ENVIRONMENT VARIABLES =================
load_dotenv()

# ================= GEMINI CLIENT =================
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
print("Gemini Key:", os.getenv("GEMINI_API_KEY"))

# ================= FLASK APP =================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= DATABASE CONNECTION =================
def get_db_connection():
    try:
        print("DB_HOST:", os.getenv("DB_HOST"))
        print("DB_USER:", os.getenv("DB_USER"))
        print("DB_NAME:", os.getenv("DB_NAME"))
        print("DB_PORT:", os.getenv("DB_PORT", 3306))
        
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )

        print("✅ Database Connected Successfully")
        return connection

    except Error as e:
        print("❌ Database Error:", e)
        return None

# ================= CAREER DATABASE LOADER =================
def load_careers():
    base_dir=os.path.dirname(os.path.abspath(__file__))
    file_path=os.path.join(base_dir,"static","data","careers_database.json")
    with open(file_path,"r",encoding="utf-8") as f:
        data=json.load(f)
    if isinstance(data,dict) and "careers" in data:
        data=data["careers"]
    if isinstance(data,dict):
        return list(data.values())
    if isinstance(data,list):
        return data
    return []

# ================= OTP STORAGE =================
otp_storage = {}

# ================= EMAIL FUNCTION =================
def send_email_otp(receiver_email, otp):
    try:
        import requests

        brevo_api_key = os.getenv("BREVO_API_KEY")

        print("Brevo API Key Loaded:", "YES" if brevo_api_key else "NO")

        if not brevo_api_key:
            print("❌ BREVO_API_KEY not found")
            return False

        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": brevo_api_key,
            "content-type": "application/json"
        }

        data = {
            "sender": {
                "name": "Smart AI Career Guide",
                "email": "smartaicareerguide001@gmail.com"
            },
            "to": [
                {
                    "email": receiver_email
                }
            ],
            "subject": "Smart AI Career Guide - Email Verification",
            "htmlContent": f"""
                <html>
                <body>
                    <h2>Smart AI Career Guide</h2>

                    <p>Hello,</p>

                    <p>Your OTP for email verification is:</p>

                    <h1>{otp}</h1>

                    <p>This OTP is valid for 10 minutes.</p>

                    <p>Thank you,<br>
                    Smart AI Career Guide Team</p>
                </body>
                </html>
            """
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        print("Brevo Status Code:", response.status_code)
        print("Brevo Response:", response.text)

        if response.status_code in [200, 201]:
            print("✅ OTP SENT SUCCESSFULLY")
            return True

        print("❌ BREVO EMAIL FAILED")
        return False

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return False
# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")


# ================= SEND OTP =================
@app.route("/send-otp", methods=["POST"])
def send_otp():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"message": "Invalid request"}), 400

        email = data.get("email")

        if not email:
            return jsonify({"message": "Email is required"}), 400

        otp = str(random.randint(100000, 999999))

        otp_storage[email] = {
            "otp": otp,
            "timestamp": datetime.now()
        }

        print(f"OTP for {email}: {otp}")

        success = send_email_otp(email, otp)

        if success:
            return jsonify({
                "status": "success",
                "message": "OTP sent successfully!"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send OTP. Check SMTP settings."
            }), 500

    except Exception as e:
        print("SEND OTP ERROR:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        mobile = request.form["mobile"]
        dob = request.form["dob"]
        user_otp = request.form["otp"]
        
        # Calculate age
        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        
        # OTP Verification
        if email not in otp_storage:
            return render_template("register.html", error="OTP expired or not sent")
        
        stored_data = otp_storage[email]
        if stored_data['otp'] != user_otp:
            return render_template("register.html", error="Invalid OTP")
        
        # Check if OTP is expired (10 minutes)
        if datetime.now() - stored_data['timestamp'] > timedelta(minutes=10):
            del otp_storage[email]
            return render_template("register.html", error="OTP expired")
        
        db = get_db_connection()
        if not db:
            return render_template("register.html", error="Database connection error")
        
        cursor = db.cursor(dictionary=True)
        
        # Check existing user
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return render_template("register.html", error="Email already registered")
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password, dob, age, mobile, verified) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (name, email, password, dob, age, mobile, 1)
        )
        db.commit()
        cursor.close()
        db.close()
        
        # Clear OTP
        del otp_storage[email]
        
        return render_template("register.html", success=True)

        return render_template("register.html", error="Email already exists")
    
    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        db = get_db_connection()
        if not db:
            return "Database connection error"
        
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user:
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            return redirect("/dashboard")
        
        return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id=session["user_id"]
    db=get_db_connection()

    if not db:
        return "Database connection error"

    cursor=db.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM psychometric_data WHERE user_id=%s LIMIT 1",
            (user_id,)
        )
        psych_record=cursor.fetchone()

        cursor.execute(
            "SELECT id FROM career_test_data WHERE user_id=%s LIMIT 1",
            (user_id,)
        )
        career_record=cursor.fetchone()

        psych_completed=psych_record is not None
        career_completed=career_record is not None

        result=None

        if psych_completed and career_completed:
            cursor.execute(
                "SELECT * FROM career_test_data WHERE user_id=%s LIMIT 1",
                (user_id,)
            )
            result=cursor.fetchone()

        return render_template(
            "dashboard.html",
            psych_completed=psych_completed,
            career_completed=career_completed,
            result=result
        )

    except Exception as e:
        print("Dashboard Error:",e)
        return f"Dashboard Error: {e}",500

    finally:
        cursor.close()
        db.close()

# ================= PSYCHOMETRIC TEST =================
@app.route("/psychometric-test")
def psychometric_test():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("psychometric_test.html")


@app.route("/submit-psychometric", methods=["POST"])
def submit_psychometric():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    db = None
    cursor = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        answers = data.get("answers", [])

        if not isinstance(answers, list) or len(answers) == 0:
            return jsonify({
                "success": False,
                "message": "No psychometric answers received"
            }), 400

        technical = 0
        creative = 0
        social = 0
        business = 0

        # Calculate latest attempt scores
        for ans in answers:

            if not isinstance(ans, dict):
                continue

            category = ans.get("category")
            score = ans.get("score", 0)

            try:
                score = int(score)
            except (TypeError, ValueError):
                score = 0

            if category == "technical":
                technical += score

            elif category == "creative":
                creative += score

            elif category == "social":
                social += score

            elif category == "business":
                business += score

        user_id = session["user_id"]

        db = get_db_connection()

        if not db:
            return jsonify({
                "success": False,
                "message": "Database connection error"
            }), 500

        cursor = db.cursor()

        # REMOVE PREVIOUS ATTEMPT
        cursor.execute(
            """
            DELETE FROM psychometric_data
            WHERE user_id = %s
            """,
            (user_id,)
        )

        # REMOVE OLD CAREER RESULT
        cursor.execute(
            """
            DELETE FROM career_results
            WHERE user_id = %s
            """,
            (user_id,)
        )

        # SAVE NEW ATTEMPT
        cursor.execute(
            """
            INSERT INTO psychometric_data
            (
                user_id,
                technical_score,
                creative_score,
                social_score,
                business_score
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                technical,
                creative,
                social,
                business
            )
        )

        db.commit()

        return jsonify({
            "success": True,
            "message": "Psychometric Test Saved Successfully",
            "scores": {
                "technical": technical,
                "creative": creative,
                "social": social,
                "business": business
            }
        })

    except Exception as e:

        if db:
            db.rollback()

        print("Psychometric Submission Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()

# ================= CAREER TEST =================
@app.route("/career-test")
def career_test():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("career_test.html")

    cursor=db.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM career_test_data WHERE user_id=%s LIMIT 1",
            (session["user_id"],)
        )
        completed=cursor.fetchone()

        return render_template(
            "career_test.html",
            assessment_completed=bool(completed)
        )

    except Exception as e:
        print("Career Test Page Error:",e)
        return f"Career Test Error: {e}"

    finally:
        cursor.close()
        db.close()

# ================= SUBMIT CAREER TEST =================
@app.route("/submit-career-test", methods=["POST"])
def submit_career_test():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Login required"
        }), 401

    db = None
    cursor = None

    try:
        user_id = session["user_id"]

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        answers = data.get("answers", {})

        if not isinstance(answers, dict):
            return jsonify({
                "success": False,
                "message": "Invalid career test answers"
            }), 400

        db = get_db_connection()

        if not db:
            return jsonify({
                "success": False,
                "message": "Database connection error"
            }), 500

        cursor = db.cursor()


        # DELETE PREVIOUS CAREER TEST ATTEMPT

        cursor.execute(
            """
            DELETE FROM career_test_data
            WHERE user_id = %s
            """,
            (user_id,)
        )

        # DELETE OLD CAREER RESULT
        # Latest test data must generate a new result

        cursor.execute(
            """
            DELETE FROM career_results
            WHERE user_id = %s
            """,
            (user_id,)
        )

        # SAVE NEW CAREER TEST ATTEMPT

        cursor.execute(
            """
            INSERT INTO career_test_data
            (
                user_id,
                career_answers
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                user_id,
                json.dumps(answers)
            )
        )

        db.commit()

        print(
            f"Career Test updated successfully for user {user_id}"
        )

        return jsonify({
            "success": True,
            "message": "Career Test Completed Successfully",
            "redirect": "/dashboard"
        })

    except Exception as e:

        if db:
            db.rollback()

        print("Career Test Error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()

# ================= CAREER PREDICTION ENGINE =================
def load_careers():
    file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"static","data","careers_database.json")
    with open(file_path,"r",encoding="utf-8") as f:
        data=json.load(f)
    careers=data.get("careers",[]) if isinstance(data,dict) else data
    return careers if isinstance(careers,list) else []

def normalize_list(value):
    if isinstance(value,list):
        return [str(x).strip().lower() for x in value if str(x).strip()]
    if isinstance(value,str):
        try:
            parsed=json.loads(value)
            if isinstance(parsed,list):
                return [str(x).strip().lower() for x in parsed if str(x).strip()]
        except:
            pass
        return [x.strip().lower() for x in value.split(",") if x.strip()]
    return []

def normalize_text(value):
    if isinstance(value,list):
        return " ".join(str(x) for x in value).lower()
    return str(value or "").strip().lower()

def subject_match(user_subjects,career_subjects):
    user_subjects=normalize_list(user_subjects)
    career_subjects=normalize_list(career_subjects)
    if not career_subjects:
        return 50
    matches=0
    for required in career_subjects:
        required=required.lower()
        if any(required in user or user in required for user in user_subjects):
            matches+=1
    return round((matches/len(career_subjects))*100,2)

def keyword_match(user_values,career_values):
    user_values=normalize_list(user_values)
    career_values=normalize_list(career_values)
    if not career_values:
        return 50
    user_text=" ".join(user_values)
    matches=0
    for item in career_values:
        item=item.lower()
        if item in user_text or any(word in user_text for word in item.replace("-"," ").replace("/"," ").split() if len(word)>3):
            matches+=1
    return round((matches/len(career_values))*100,2)

def calculate_career_match(career,psychometric,answers):
    favorite=normalize_list(answers.get("favorite_subjects",[]))
    weak=normalize_list(answers.get("weak_subjects",[]))
    interests=normalize_list(answers.get("interests",[]))
    hobbies=normalize_list(answers.get("hobbies",[]))
    strengths=normalize_list(answers.get("strengths",[]))
    career_goals=normalize_list(answers.get("career_goal",[]))
    qualification=normalize_text(answers.get("qualification",""))
    work_environment=normalize_text(answers.get("work_environment",""))
    work_style=normalize_text(answers.get("work_style",""))
    work_life=normalize_text(answers.get("work_life",""))
    higher_studies=normalize_text(answers.get("higher_studies",""))
    relocation=normalize_text(answers.get("relocation",""))
    dream_job=normalize_text(answers.get("dream_job",""))
    additional_info=normalize_text(answers.get("additional_info",""))
    all_profile_text=" ".join(favorite+interests+hobbies+strengths+career_goals+[qualification,work_environment,work_style,work_life,higher_studies,relocation,dream_job,additional_info])

    required=career.get("required_subjects",[])
    optional=career.get("optional_subjects",[])
    career_interests=career.get("interests",[])
    career_skills=career.get("skills",[])
    personality_fit=career.get("personality_fit",{})
    category=normalize_text(career.get("category",""))
    career_name=normalize_text(career.get("name",""))
    if career_name == "software developer":
        print("DEBUG USER INTERESTS:", interests)
        print("DEBUG USER HOBBIES:", hobbies)
        print("DEBUG USER STRENGTHS:", strengths)
        print("DEBUG USER SUBJECTS:", favorite)
        print("DEBUG CAREER INTERESTS:", career_interests)
        print("DEBUG CAREER SKILLS:", career_skills)
        print("DEBUG REQUIRED SUBJECTS:", required)

    required_score=subject_match(favorite,required)
    optional_score=subject_match(favorite,optional) if optional else 50
    weak_penalty=0
    for subject in normalize_list(required):
        if any(subject in weak or weak in subject for weak in normalize_list(weak)):
            weak_penalty+=15
    academic_score=max(0,round((required_score*0.75)+(optional_score*0.25)-weak_penalty,2))

    try:
        cgpa=float(str(answers.get("cgpa","")).replace("%","").strip())
        if cgpa>10:
            cgpa=min(cgpa,100)
            academic_performance=cgpa
        else:
            academic_performance=min(cgpa*10,100)
        academic_score=round((academic_score*0.75)+(academic_performance*0.25),2)
    except:
        pass

    psych_matches=[]
    for trait,target in personality_fit.items():
        try:
            user_score=float(psychometric.get(f"{trait}_score",0))
            normalized_user=min((user_score/125)*100,100)
            target=float(target)
            match=max(0,100-abs(normalized_user-target))
            psych_matches.append(match)
        except:
            continue
    psychometric_score=round(sum(psych_matches)/len(psych_matches),2) if psych_matches else 50

    interest_score=keyword_match(interests+hobbies,career_interests)
    skill_score=keyword_match(strengths,career_skills)

    goal_category_map={
        "technology":["technology","tech"],
        "business":["business","entrepreneurship"],
        "healthcare":["healthcare"],
        "government":["government"],
        "education":["education"],
        "research":["research"],
        "creative arts":["creative","creative arts"],
        "law":["law"],
        "finance":["finance"],
        "media":["media"],
        "entrepreneurship":["business","entrepreneurship"]
    }

    goal_score=50
    if career_goals:
        goal_hits=0
        for goal in career_goals:
            goal=goal.lower()
            if goal=="still exploring":
                continue
            possible=goal_category_map.get(goal,[goal])
            if any(x in category or x in career_name for x in possible):
                goal_hits+=1
        goal_score=round((goal_hits/max(len([g for g in career_goals if g!="still exploring"]),1))*100,2)

    dream_score=0
    if dream_job:
        dream_words=[w for w in dream_job.replace("/"," ").replace("-"," ").split() if len(w)>2]
        dream_hits=sum(1 for word in dream_words if word in career_name or word in category)
        dream_score=round((dream_hits/max(len(dream_words),1))*100,2)

    profile_interest=round((interest_score*0.45)+(skill_score*0.30)+(goal_score*0.15)+(dream_score*0.10),2)

    work_score=50
    if work_environment:
        environment_text=category+" "+career_name+" "+normalize_text(career.get("description",""))
        if work_environment in environment_text:
            work_score=100

    work_style_score=50
    if work_style=="individually":
        work_style_score=70
    elif work_style=="in a team":
        work_style_score=70
    elif work_style=="both":
        work_style_score=90

    lifestyle_score=50
    if work_life:
        lifestyle_text=normalize_text(career.get("growth_prospects",""))+" "+normalize_text(career.get("salary_range",""))
        if work_life=="career growth" and "excellent" in lifestyle_text:
            lifestyle_score=90
        elif work_life=="high salary" and "$" in lifestyle_text:
            lifestyle_score=85
        elif work_life=="job security":
            lifestyle_score=65
        elif work_life=="social impact" and any(x in category for x in ["health","social","education","government"]):
            lifestyle_score=90

    preference_score=round((work_score*0.40)+(work_style_score*0.25)+(lifestyle_score*0.35),2)

    total_score=round(
        (academic_score*0.25)+
        (psychometric_score*0.35)+
        (profile_interest*0.25)+
        (preference_score*0.15),
        2
    )

    if required_score==0:
        total_score=round(total_score*0.85,2)

    return {
        "total_score":min(total_score,99),
        "academic_score":academic_score,
        "psychometric_score":psychometric_score,
        "interest_score":profile_interest,
        "confidence":min(round(total_score,2),99)
    }

def generate_career_roadmap(career):
    education=career.get("education","")
    required=career.get("required_subjects",[])
    skills=career.get("skills",[])
    interests=career.get("interests",[])
    growth=career.get("growth_prospects","")

    roadmap=[]

    if education:
        roadmap.append({
            "step":1,
            "title":"Build Your Educational Foundation",
            "description":f"Complete the recommended educational pathway: {education}."
        })

    if required:
        roadmap.append({
            "step":len(roadmap)+1,
            "title":"Strengthen Core Subjects",
            "description":"Focus on: "+", ".join(required)+"."
        })

    if skills:
        roadmap.append({
            "step":len(roadmap)+1,
            "title":"Develop Career Skills",
            "description":"Build practical skills in: "+", ".join(skills)+"."
        })

    roadmap.append({
        "step":len(roadmap)+1,
        "title":"Build Practical Experience",
        "description":"Create projects, complete practical assignments, participate in internships and build a portfolio related to this career."
    })

    if interests:
        roadmap.append({
            "step":len(roadmap)+1,
            "title":"Explore Your Career Interests",
            "description":"Explore areas such as "+", ".join(interests)+"."
        })

    roadmap.append({
        "step":len(roadmap)+1,
        "title":"Prepare for Employment",
        "description":"Prepare your resume, portfolio, interviews and relevant technical or professional certifications."
    })

    if growth:
        roadmap.append({
            "step":len(roadmap)+1,
            "title":"Plan Long-Term Growth",
            "description":growth
        })

    return roadmap
    
@app.route("/generate-result")
def generate_result():
    if "user_id" not in session:
        return redirect("/login")

    db=get_db_connection()
    if not db:
        return "Database connection error"

    cursor=db.cursor(dictionary=True)

    try:
        user_id=session["user_id"]

        cursor.execute(
            "SELECT * FROM psychometric_data WHERE user_id=%s ORDER BY test_date DESC LIMIT 1",
            (user_id,)
        )
        psychometric=cursor.fetchone()

        cursor.execute(
            "SELECT * FROM career_test_data WHERE user_id=%s ORDER BY test_date DESC LIMIT 1",
            (user_id,)
        )
        career_test=cursor.fetchone()

        if not psychometric or not career_test:
            return redirect("/dashboard")

        try:
            answers=json.loads(career_test.get("career_answers","{}"))
        except:
            answers={}
        print("DEBUG RAW CAREER ANSWERS:", answers)

        careers=load_careers()
        career_matches=[]

        # Existing recommendation engine
        for career in careers:
            if not isinstance(career,dict) or not career.get("name"):
                continue

            scores=calculate_career_match(
                career,
                psychometric,
                answers
            )

            career_matches.append({
                "career":career,
                "scores":scores
            })

        if len(career_matches)<3:
            return "Career prediction requires at least 3 valid career records."

           # ================= ML PERSONALIZATION =================
        from ml.feature_mapper import map_existing_data_to_ml_features
        from ml.predictor import predict_careers
        from ml.career_mapping import map_ml_career_to_app_career

        ml_features = map_existing_data_to_ml_features(
            psychometric,
            answers
        )

        ml_predictions = predict_careers(ml_features)

        # Keep ML predictions as an additional signal.
        # Do NOT give unsupported careers an ML score of 0,
        # because the trained model currently contains only 6 classes.
        ml_scores = {}

        for prediction in ml_predictions:
            app_career = map_ml_career_to_app_career(
                prediction["career"]
            )

            if app_career:
                ml_scores[app_career.lower()] = prediction["probability"]

        # Existing engine remains the primary recommendation system.
        # ML provides an additional bonus only when it recognizes
        # the career directly.
        for match in career_matches:
            career_name = match["career"]["name"]

            existing_score = match["scores"]["total_score"]

            ml_score = ml_scores.get(
                career_name.lower(),
                0
            )

            # ML contributes up to 10% only when applicable.
            ml_bonus = ml_score * 0.10

            match["scores"]["ml_score"] = round(
                ml_score,
                2
            )

            match["scores"]["total_score"] = round(
                min(existing_score + ml_bonus, 99),
                2
            )

            match["scores"]["confidence"] = round(
                min(match["scores"]["total_score"], 99),
                2
            )

        # Rank ALL careers from careers_database.json
        career_matches.sort(
            key=lambda x: x["scores"]["total_score"],
            reverse=True
        )

        # Existing result page continues showing the best 3
        top_3 = career_matches[:3]
        print("CAREER RANKING DEBUG:")
        for match in career_matches:
            print(
                match["career"]["name"],
                "TOTAL:", match["scores"]["total_score"],
                "ACADEMIC:", match["scores"].get("academic_score"),
                "PSYCHOMETRIC:", match["scores"].get("psychometric_score"),
                "INTEREST:", match["scores"].get("interest_score"),
                "ML:", match["scores"].get("ml_score")
            )
        roadmap=generate_career_roadmap(top_3[0]["career"])

        cursor.execute(
            "DELETE FROM career_results WHERE user_id=%s",
            (user_id,)
        )

        cursor.execute("""
            INSERT INTO career_results
            (
                user_id,
                primary_career,
                primary_confidence,
                primary_score,
                secondary_career,
                secondary_confidence,
                secondary_score,
                alternative_career,
                alternative_confidence,
                alternative_score,
                academic_score,
                psychometric_score,
                interest_score
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(
            user_id,
            top_3[0]["career"]["name"],
            top_3[0]["scores"]["confidence"],
            top_3[0]["scores"]["total_score"],
            top_3[1]["career"]["name"],
            top_3[1]["scores"]["confidence"],
            top_3[1]["scores"]["total_score"],
            top_3[2]["career"]["name"],
            top_3[2]["scores"]["confidence"],
            top_3[2]["scores"]["total_score"],
            top_3[0]["scores"]["academic_score"],
            top_3[0]["scores"]["psychometric_score"],
            top_3[0]["scores"]["interest_score"]
        ))
        
        db.commit()
        return redirect("/result")

    except Exception as e:
        db.rollback()
        print("Career Prediction Error:",e)
        return f"Career Prediction Error: {e}"

    finally:
        cursor.close()
        db.close()

# ================= RESULT PAGE =================
@app.route("/result")
def result():
    if "user_id" not in session:
        return redirect("/login")

    db=get_db_connection()
    if not db:
        return "Database connection error"

    cursor=db.cursor(dictionary=True)

    try:
        user_id=session["user_id"]

        cursor.execute(
            "SELECT * FROM career_results WHERE user_id=%s ORDER BY result_date DESC LIMIT 1",
            (user_id,)
        )
        result_data=cursor.fetchone()

        if not result_data:
            return redirect("/dashboard")

        careers=load_careers()
        career_details={}

        for career in careers:
            if not isinstance(career,dict):
                continue

            name=career.get("name","")

            if name==result_data.get("primary_career"):
                career_details["primary"]=career
            elif name==result_data.get("secondary_career"):
                career_details["secondary"]=career
            elif name==result_data.get("alternative_career"):
                career_details["alternative"]=career

        primary=career_details.get("primary",{})
        roadmap=generate_career_roadmap(primary)

        profile_analysis={
            "psychometric":round(float(result_data.get("psychometric_score") or 0),2),
            "academic":round(float(result_data.get("academic_score") or 0),2),
            "interests":round(float(result_data.get("interest_score") or 0),2)
        }

        return render_template(
            "result.html",
            result=result_data,
            careers=career_details,
            roadmap=roadmap,
            profile_analysis=profile_analysis
        )

    except Exception as e:
        print("Result Page Error:",e)
        return f"Result Page Error: {e}"

    finally:
        cursor.close()
        db.close()

# ================= AI CHATBOT =================
@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("chatbot.html")

@app.route('/chat_api', methods=['POST'])
def chat_api():
    try:
        # Get user message
        data = request.get_json()
        user_message = data.get("message")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Optional: get user session
        user_id = session.get("user_id", None)
        session_id = f"{user_id}_session" if user_id else "guest_session"

        # System prompt (your AI behavior)
        system_prompt = """
        You are a helpful career guidance counselor for the Smart AI Career Guide platform.
        Help users with:
        - Career suggestions
        - Skills required
        - Roadmaps
        - Learning resources

        Keep answers simple, clear, and helpful.
        """

        # Combine prompt + user input
        full_prompt = system_prompt + "\nUser: " + user_message

        # Generate response from Gemini
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=full_prompt
        )

        ai_reply = response.text

        # Save chat to database
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO chat_history (user_id, session_id, role, message)
                VALUES (%s, %s, %s, %s)
            """, (user_id, session_id, "user", user_message))

            cursor.execute("""
                INSERT INTO chat_history (user_id, session_id, role, message)
                VALUES (%s, %s, %s, %s)
            """, (user_id, session_id, "ai", ai_reply))

            db.commit()
            cursor.close()
            db.close()

        except Exception as db_error:
            print("DB Error:", db_error)

        return jsonify({
            "reply": ai_reply
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Something went wrong"}), 500

# ================= CAREER SUPPORT =================
@app.route("/career-support")
def career_support():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("career_support.html")

@app.route("/submit-career-booking", methods=["POST"])
def submit_advisor_booking():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    try:

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        preferred_date = request.form.get("preferred_date")
        preferred_time = request.form.get("preferred_time")
        message = request.form.get("message", "")

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO advisor_bookings
            (user_id, name, email, phone, preferred_date, preferred_time, message, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            name,
            email,
            phone,
            preferred_date,
            preferred_time,
            message,
            "Pending"
        ))

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Booking Submitted Successfully!"
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "Booking Failed!"
        }), 500

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, render_template, request, redirect, session, jsonify, url_for