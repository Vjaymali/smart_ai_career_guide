let sections=[];
let currentSection=0;
let answers={};

const formContent=document.getElementById("formContent");
const progress=document.getElementById("progress");
const progressText=document.getElementById("progressText");
const prevBtn=document.getElementById("prevBtn");
const nextBtn=document.getElementById("nextBtn");
const loadingScreen=document.getElementById("loadingScreen");

async function loadCareerTest(){

    try{

        const response=await fetch("/static/data/career_test.json");

        sections=await response.json();

        loadSection();

    }catch(error){

        console.error(error);

        formContent.innerHTML=`
            <div class="error-box">
                <h2>Unable to Load Career Test</h2>
                <p>Please check career_test.json.</p>
            </div>
        `;

    }

}

function updateProgress(){

    const percent=((currentSection+1)/sections.length)*100;

    progress.style.width=percent+"%";

    progressText.innerHTML=`Section ${currentSection+1} of ${sections.length}`;

}

function loadSection(){

    updateProgress();

    const section=sections[currentSection];

    let html=`
        <div class="section-title">${section.title}</div>
        <div class="section-subtitle">${section.subtitle}</div>
    `;

    section.questions.forEach(question=>{

        html+=renderQuestion(question);

    });

    formContent.innerHTML=html;

    restoreAnswers();

    prevBtn.style.display=currentSection===0?"none":"inline-block";

    nextBtn.innerHTML=currentSection===sections.length-1?
    'Submit <i class="fas fa-check"></i>':
    'Next <i class="fas fa-arrow-right"></i>';

}

window.onload=loadCareerTest;

function renderQuestion(question){

    let html=`<div class="input-group">
    <label>${question.label}</label>`;

    switch(question.type){

        case "text":

            html+=`
            <input
            type="text"
            id="${question.id}"
            placeholder="Enter here">
            `;

        break;

        case "number":

            html+=`
            <input
            type="number"
            id="${question.id}">
            `;

        break;

        case "textarea":

            html+=`
            <textarea
            id="${question.id}"
            rows="4"
            placeholder="Write your answer..."></textarea>
            `;

        break;

        case "select":

            html+=`
            <select id="${question.id}">
            <option value="">Select</option>
            `;

            question.options.forEach(option=>{

                html+=`<option value="${option}">${option}</option>`;

            });

            html+=`</select>`;

        break;

        case "radio":

            html+=`<div class="checkbox-grid">`;

            question.options.forEach(option=>{

                html+=`
                <label class="checkbox-card">

                <input
                type="radio"
                name="${question.id}"
                value="${option}">

                ${option}

                </label>
                `;

            });

            html+=`</div>`;

        break;

        case "checkbox":

            html+=`<div class="checkbox-grid">`;

            question.options.forEach(option=>{

                html+=`
                <label class="checkbox-card">

                <input
                type="checkbox"
                data-id="${question.id}"
                value="${option}">

                ${option}

                </label>
                `;

            });

            html+=`</div>`;

        break;

    }

    html+=`</div>`;

    return html;

}

function saveAnswers(){

    const section=sections[currentSection];

    section.questions.forEach(question=>{

        switch(question.type){

            case "text":
            case "number":
            case "textarea":
            case "select":

                answers[question.id]=document.getElementById(question.id).value;

            break;

            case "radio":

                const radio=document.querySelector(`input[name="${question.id}"]:checked`);

                answers[question.id]=radio?radio.value:"";

            break;

            case "checkbox":

                answers[question.id]=[];

                document.querySelectorAll(`input[data-id="${question.id}"]:checked`).forEach(item=>{

                    answers[question.id].push(item.value);

                });

            break;

        }

    });

}

function restoreAnswers(){

    const section=sections[currentSection];

    section.questions.forEach(question=>{

        if(!(question.id in answers)) return;

        switch(question.type){

            case "text":
            case "number":
            case "textarea":
            case "select":

                document.getElementById(question.id).value=answers[question.id];

            break;

            case "radio":

                document.querySelectorAll(`input[name="${question.id}"]`).forEach(item=>{

                    if(item.value===answers[question.id]){

                        item.checked=true;

                    }

                });

            break;

            case "checkbox":

                document.querySelectorAll(`input[data-id="${question.id}"]`).forEach(item=>{

                    if(answers[question.id].includes(item.value)){

                        item.checked=true;

                    }

                });

            break;

        }

    });

}

prevBtn.onclick=function(){

    saveAnswers();

    if(currentSection>0){

        currentSection--;

        loadSection();

    }

};

nextBtn.onclick=function(){

    saveAnswers();

    if(currentSection<sections.length-1){

        currentSection++;

        loadSection();

    }else{

        submitCareerTest();

    }

};

async function submitCareerTest(){

    loadingScreen.classList.add("active");

    try{

        const response=await fetch("/submit-career-test",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                answers:answers
            })

        });

        const data=await response.json();

        loadingScreen.classList.remove("active");

        if(data.success){

            alert("Career Test Submitted Successfully!");

            window.location.href="/dashboard";

        }else{

            alert(data.message);

        }

    }catch(error){

        console.error(error);

        loadingScreen.classList.remove("active");

        alert("Server Error");

    }

}

document.addEventListener("keydown",function(e){

    if(e.key==="ArrowRight"){

        nextBtn.click();

    }

    if(e.key==="ArrowLeft"){

        prevBtn.click();

    }

});
