/*=========================================
PSYCHOMETRIC TEST
=========================================*/

const questions = [

{ q: "I enjoy solving logical problems.", type: "technical" },
{ q: "I like designing or creating new things.", type: "creative" },
{ q: "I enjoy helping people solve their problems.", type: "social" },
{ q: "I like taking leadership and managing tasks.", type: "business" },
{ q: "I am interested in coding or technology.", type: "technical" },
{ q: "I enjoy drawing, writing, or content creation.", type: "creative" },
{ q: "I communicate well with others.", type: "social" },
{ q: "I like business ideas and startups.", type: "business" },
{ q: "I enjoy mathematics and analysis.", type: "technical" },
{ q: "I think creatively to solve problems.", type: "creative" },
{ q: "I like teamwork and collaboration.", type: "social" },
{ q: "I take initiative in projects.", type: "business" },
{ q: "I enjoy working with computers.", type: "technical" },
{ q: "I like visual storytelling.", type: "creative" },
{ q: "I understand others' emotions easily.", type: "social" },
{ q: "I like planning and organizing.", type: "business" },
{ q: "I enjoy learning new technologies.", type: "technical" },
{ q: "I have a strong imagination.", type: "creative" },
{ q: "I enjoy public speaking.", type: "social" },
{ q: "I am confident taking risks.", type: "business" },
{ q: "I like problem-solving challenges.", type: "technical" },
{ q: "I enjoy creative thinking tasks.", type: "creative" },
{ q: "I help others when they need support.", type: "social" },
{ q: "I like decision making.", type: "business" },
{ q: "I enjoy analytical thinking.", type: "technical" }

];

/*=========================================
VARIABLES
=========================================*/

let current = 0;

let answers = new Array(questions.length).fill(null);

/*=========================================
LOAD QUESTION
=========================================*/

function loadQuestion() {

const questionBox = document.getElementById("question-box");

const counter = document.getElementById("questionCounter");

const progress = document.getElementById("progress");

const progressText = document.getElementById("progressText");

const nextBtn = document.getElementById("nextBtn");

questionBox.style.opacity = "0";

Swal.fire({

    icon: "success",

    title: "Assessment Completed!",

    text: "Your Psychometric Test has been submitted successfully.",

    confirmButtonColor: "#7c3aed"

}).then(() => {

    window.location.href="/career-test";

});

counter.innerText =
`Question ${current+1} of ${questions.length}`;

let percentage =
((current+1)/questions.length)*100;

progress.style.width = percentage + "%";

progressText.innerText =
Math.round(percentage)+"%";

/*-------------------------
RESET OPTIONS
--------------------------*/

let buttons =
document.querySelectorAll(".options button");

buttons.forEach(btn=>{

btn.classList.remove("selected");

});

/*-------------------------
PREVIOUS ANSWER
--------------------------*/

if(answers[current]!==null){

buttons[answers[current]-1]
.classList.add("selected");

}

/*-------------------------
NEXT BUTTON
--------------------------*/

if(current===questions.length-1){

nextBtn.innerHTML =
'Submit Assessment <i class="fas fa-paper-plane"></i>';

nextBtn.classList.add("finish-btn");

}else{

nextBtn.innerHTML =
'Next <i class="fas fa-arrow-right"></i>';

nextBtn.classList.remove("finish-btn");

}

}

/*=========================================
SELECT ANSWER
=========================================*/

function selectAnswer(value){

answers[current]=value;

let buttons =
document.querySelectorAll(".options button");

buttons.forEach(btn=>{

btn.classList.remove("selected");

});

buttons[value-1]
.classList.add("selected");

}

/*=========================================
NEXT
=========================================*/

function nextQuestion(){

if(answers[current]===null){

alert("Please select an answer before continuing.");

return;

}

if(current<questions.length-1){

current++;

loadQuestion();

}else{

submitTest();

}

}

/*=========================================
PREVIOUS
=========================================*/

function prevQuestion(){

if(current>0){

current--;

loadQuestion();

}

}

/*=========================================
SUBMIT TEST
=========================================*/

function submitTest() {

    // Show AI Loading Screen
    const loading = document.getElementById("loadingScreen");

    if (loading) {
        loading.classList.add("active");
    }

    // Prepare answers for database
    let finalAnswers = [];

    for (let i = 0; i < questions.length; i++) {

        finalAnswers.push({

            question_no: i + 1,

            question: questions[i].q,

            category: questions[i].type,

            score: answers[i]

        });

    }

    fetch("/submit-psychometric", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            answers: finalAnswers

        })

    })

    .then(response => {

        if (!response.ok) {
            throw new Error("Server Error");
        }

        return response.json();

    })

    .then(data => {

        console.log("Psychometric Saved:", data);

        setTimeout(() => {

            window.location.href = "/career-test";

        }, 2500);

    })

    .catch(error => {

        console.error(error);

        if (loading) {
            loading.classList.remove("active");
        }

        alert("Something went wrong while saving your responses.");

    });

}

/*=========================================
PREVENT ENTER KEY SUBMIT
=========================================*/

document.addEventListener("keydown", function(e){

    if(e.key==="Enter"){

        e.preventDefault();

    }

});

/*=========================================
PAGE LOAD
=========================================*/

window.onload=function(){

    loadQuestion();

};

/*=========================================
OPTION ANIMATION
=========================================*/

document.querySelectorAll(".options button").forEach(button=>{

button.addEventListener("click",function(){

this.animate([

{

transform:"scale(.95)"

},

{

transform:"scale(1.03)"

},

{

transform:"scale(1)"

}

],{

duration:250

});

});

});

/*=========================================
SMOOTH QUESTION TRANSITION
=========================================*/

function animateQuestion(){

const card=document.querySelector(".question-card");

card.style.opacity="0";

card.style.transform="translateY(20px)";

setTimeout(()=>{

card.style.opacity="1";

card.style.transform="translateY(0px)";

},180);

}

/*=========================================
OVERRIDE LOAD
=========================================*/

const oldLoadQuestion=loadQuestion;

loadQuestion=function(){

animateQuestion();

oldLoadQuestion();

};

/*=========================================
DISABLE NEXT UNTIL OPTION SELECTED
=========================================*/

const originalSelect=selectAnswer;

selectAnswer=function(value){

originalSelect(value);

document.getElementById("nextBtn").disabled=false;

};

/*=========================================
AUTO SCROLL
=========================================*/

function scrollTopSmooth(){

window.scrollTo({

top:0,

behavior:"smooth"

});

}

const oldNext=nextQuestion;

nextQuestion=function(){

oldNext();

scrollTopSmooth();

};

const oldPrev=prevQuestion;

prevQuestion=function(){

oldPrev();

scrollTopSmooth();

};