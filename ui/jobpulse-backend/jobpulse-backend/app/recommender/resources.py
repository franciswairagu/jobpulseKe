"""Curated, provider-owned resources for common technical skill gaps.

Each course entry includes (title, provider, url, duration, difficulty).
Interview practice entries include (title, provider, url, duration, format).
"""

from urllib.parse import quote_plus

from .models import InterviewPracticeRecommendation, LearningRecommendation


# (title, provider, url, duration, difficulty)
COURSES = {
    # Programming Languages
    "python": ("Python for Everybody", "Coursera", "https://www.coursera.org/specializations/python", "4 months", "Beginner"),
    "java": ("Java Programming Masterclass", "Udemy", "https://www.udemy.com/course/java-the-complete-java-developer-course/", "80 hours", "Beginner"),
    "javascript": ("The Complete JavaScript Course", "Udemy", "https://www.udemy.com/course/the-complete-javascript-course/", "60 hours", "Beginner"),
    "typescript": ("Understanding TypeScript", "Udemy", "https://www.udemy.com/course/understanding-typescript/", "15 hours", "Intermediate"),
    "go": ("Go: The Complete Developer's Guide", "Udemy", "https://www.udemy.com/course/go-the-complete-developers-guide/", "25 hours", "Intermediate"),
    "golang": ("Go: The Complete Developer's Guide", "Udemy", "https://www.udemy.com/course/go-the-complete-developers-guide/", "25 hours", "Intermediate"),
    "rust": ("Rust Programming", "Coursera", "https://www.coursera.org/learn/rust-programming", "6 weeks", "Intermediate"),
    "c++": ("Beginning C++ Programming", "Udemy", "https://www.udemy.com/course/beginning-c-plus-plus-programming/", "30 hours", "Beginner"),
    "c#": ("C# Advanced Topics", "Udemy", "https://www.udemy.com/course/csharp-advanced/", "12 hours", "Intermediate"),
    "php": ("PHP for Beginners", "Udemy", "https://www.udemy.com/course/php-for-complete-beginners-includes-mysql-oop/", "20 hours", "Beginner"),
    "ruby": ("The Complete Ruby on Rails Developer Course", "Udemy", "https://www.udemy.com/course/the-complete-ruby-on-rails-developer-course/", "40 hours", "Beginner"),
    "kotlin": ("Kotlin for Android Developers", "Udemy", "https://www.udemy.com/course/kotlin-for-android-developers/", "20 hours", "Intermediate"),
    "swift": ("Developing iOS Apps with Swift", "Coursera", "https://www.coursera.org/learn/app-development", "4 months", "Beginner"),
    "sql": ("SQL for Data Science", "Coursera", "https://www.coursera.org/learn/sql-for-data-science", "4 weeks", "Beginner"),
    "bash": ("Linux Command Line Basics", "Udemy", "https://www.udemy.com/course/linux-command-line-basics/", "5 hours", "Beginner"),

    # Web Frameworks
    "django": ("Django for Beginners", "Udemy", "https://www.udemy.com/course/django-for-beginners/", "15 hours", "Beginner"),
    "flask": ("Flask: Develop Web Applications in Python", "Udemy", "https://www.udemy.com/course/flask-develop-web-applications-in-python/", "10 hours", "Beginner"),
    "fastapi": ("FastAPI - The Complete Course", "Udemy", "https://www.udemy.com/course/fastapi-the-complete-course/", "12 hours", "Intermediate"),
    "react": ("React - The Complete Guide", "Udemy", "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "40 hours", "Beginner"),
    "vue": ("Vue - The Complete Guide", "Udemy", "https://www.udemy.com/course/vuejs-the-complete-guide-incl-router-vuex/", "35 hours", "Beginner"),
    "angular": ("Angular - The Complete Guide", "Udemy", "https://www.udemy.com/course/complete-guide-to-angular-2/", "35 hours", "Intermediate"),
    "next.js": ("Next.js & React - The Complete Guide", "Udemy", "https://www.udemy.com/course/nextjs-react-the-complete-guide/", "30 hours", "Intermediate"),
    "nextjs": ("Next.js & React - The Complete Guide", "Udemy", "https://www.udemy.com/course/nextjs-react-the-complete-guide/", "30 hours", "Intermediate"),
    "node.js": ("Node.js, Express, MongoDB - The Complete Bootcamp", "Udemy", "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/", "40 hours", "Beginner"),
    "nodejs": ("Node.js, Express, MongoDB - The Complete Bootcamp", "Udemy", "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/", "40 hours", "Beginner"),
    "spring boot": ("Spring Boot React Full Stack", "Udemy", "https://www.udemy.com/course/spring-boot-react-full-stack/", "25 hours", "Intermediate"),
    "laravel": ("Laravel - From Scratch", "Udemy", "https://www.udemy.com/course/laravel-from-scratch/", "20 hours", "Beginner"),
    ".net": (".NET Complete Developer's Guide", "Udemy", "https://www.udemy.com/course/complete-aspnet-mvc-course/", "30 hours", "Intermediate"),
    "asp.net": (".NET Complete Developer's Guide", "Udemy", "https://www.udemy.com/course/complete-aspnet-mvc-course/", "30 hours", "Intermediate"),

    # Cloud Platforms
    "aws": ("AWS Certified Cloud Practitioner", "Coursera", "https://www.coursera.org/professional-certificates/aws-cloud-technologist", "3 months", "Beginner"),
    "amazon web services": ("AWS Certified Cloud Practitioner", "Coursera", "https://www.coursera.org/professional-certificates/aws-cloud-technologist", "3 months", "Beginner"),
    "azure": ("Azure Fundamentals AZ-900", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/", "5 weeks", "Beginner"),
    "microsoft azure": ("Azure Fundamentals AZ-900", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/", "5 weeks", "Beginner"),
    "gcp": ("Google Cloud Fundamentals", "Coursera", "https://www.coursera.org/learn/gcp-fundamentals", "4 weeks", "Beginner"),
    "google cloud": ("Google Cloud Fundamentals", "Coursera", "https://www.coursera.org/learn/gcp-fundamentals", "4 weeks", "Beginner"),
    "terraform": ("Terraform for Beginners", "Udemy", "https://www.udemy.com/course/terraform-beginners-to-master/", "15 hours", "Beginner"),
    "docker": ("Docker & Kubernetes: The Practical Guide", "Udemy", "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/", "25 hours", "Beginner"),
    "kubernetes": ("Kubernetes for Beginners", "Udemy", "https://www.udemy.com/course/kubernetes-for-the-absolute-beginner-kvm/", "10 hours", "Beginner"),

    # Databases
    "postgresql": ("PostgreSQL for Beginners", "Udemy", "https://www.udemy.com/course/postgresql-for-beginners/", "10 hours", "Beginner"),
    "mysql": ("The Complete MySQL Bootcamp", "Udemy", "https://www.udemy.com/course/the-complete-mysql-bootcamp/", "12 hours", "Beginner"),
    "mongodb": ("The Complete MongoDB Developer Course", "Udemy", "https://www.udemy.com/course/the-complete-mongodb-developer-course/", "15 hours", "Intermediate"),
    "redis": ("Redis: From Scratch", "Udemy", "https://www.udemy.com/course/redis-from-scratch/", "8 hours", "Intermediate"),
    "elasticsearch": ("Elasticsearch Complete Guide", "Udemy", "https://www.udemy.com/course/elasticsearch-complete-guide/", "15 hours", "Intermediate"),

    # AI/ML
    "tensorflow": ("TensorFlow Developer Certificate", "Coursera", "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "4 months", "Intermediate"),
    "pytorch": ("PyTorch for Deep Learning", "Udemy", "https://www.udemy.com/course/pytorch-for-deep-learning/", "25 hours", "Intermediate"),
    "scikit-learn": ("Machine Learning with scikit-learn", "Coursera", "https://www.coursera.org/learn/machine-learning-with-python", "4 weeks", "Intermediate"),
    "sklearn": ("Machine Learning with scikit-learn", "Coursera", "https://www.coursera.org/learn/machine-learning-with-python", "4 weeks", "Intermediate"),
    "pandas": ("Data Analysis with Python and Pandas", "Udemy", "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/", "10 hours", "Beginner"),
    "numpy": ("NumPy for Data Science", "Udemy", "https://www.udemy.com/course/numpy-for-data-science/", "6 hours", "Beginner"),
    "machine learning": ("Machine Learning Specialization", "Coursera", "https://www.coursera.org/specializations/machine-learning-introduction", "3 months", "Beginner"),
    "deep learning": ("Deep Learning Specialization", "Coursera", "https://www.coursera.org/specializations/deep-learning", "5 months", "Intermediate"),
    "nlp": ("Natural Language Processing", "Coursera", "https://www.coursera.org/learn/natural-language-processing", "4 months", "Advanced"),

    # Data & Analytics
    "tableau": ("Tableau for Beginners", "Udemy", "https://www.udemy.com/course/tableau-for-beginners/", "6 hours", "Beginner"),
    "power bi": ("Microsoft Power BI Desktop", "Udemy", "https://www.udemy.com/course/microsoft-power-bi-complete/", "10 hours", "Beginner"),
    "powerbi": ("Microsoft Power BI Desktop", "Udemy", "https://www.udemy.com/course/microsoft-power-bi-complete/", "10 hours", "Beginner"),
    "excel": ("Excel Skills for Business", "Coursera", "https://www.coursera.org/specializations/excel", "4 months", "Beginner"),
    "spark": ("Big Data with PySpark", "Udemy", "https://www.udemy.com/course/big-data-with-pyspark/", "12 hours", "Intermediate"),
    "hadoop": ("Hadoop Developer In Real Time", "Udemy", "https://www.udemy.com/course/hadoop-developer-in-real-time/", "20 hours", "Intermediate"),
    "airflow": ("Apache Airflow: A Complete Guide", "Udemy", "https://www.udemy.com/course/apache-airflow/", "15 hours", "Intermediate"),
    "snowflake": ("Snowflake: From Zero to Hero", "Udemy", "https://www.udemy.com/course/snowflake-from-zero-to-hero/", "10 hours", "Intermediate"),
    "dbt": ("dbt Fundamentals", "dbt Learn", "https://courses.getdbt.com/courses/fundamentals", "6 hours", "Beginner"),

    # DevOps & Tools
    "git": ("Git Complete: The Definitive Guide", "Udemy", "https://www.udemy.com/course/git-complete/", "8 hours", "Beginner"),
    "github": ("GitHub Actions Masterclass", "Udemy", "https://www.udemy.com/course/github-actions-masterclass/", "12 hours", "Intermediate"),
    "jenkins": ("Jenkins, From Zero To Hero", "Udemy", "https://www.udemy.com/course/jenkins-from-zero-to-hero/", "15 hours", "Intermediate"),
    "terraform": ("Terraform for Beginners to Master", "Udemy", "https://www.udemy.com/course/terraform-beginners-to-master/", "15 hours", "Beginner"),
    "ansible": ("Ansible for the Absolute Beginners", "Udemy", "https://www.udemy.com/course/ansible-for-the-absolute-beginners/", "10 hours", "Beginner"),
    "grafana": ("Grafana Fundamentals", "Grafana Labs", "https://grafana.com/tutorials/", "5 hours", "Beginner"),
    "prometheus": ("Monitoring with Prometheus", "Udemy", "https://www.udemy.com/course/monitoring-with-prometheus/", "10 hours", "Intermediate"),

    # Frontend
    "html": ("HTML and CSS for Beginners", "Udemy", "https://www.udemy.com/course/html-and-css-for-beginners/", "10 hours", "Beginner"),
    "css": ("CSS Masterclass", "Udemy", "https://www.udemy.com/course/css-masterclass/", "15 hours", "Beginner"),
    "tailwind": ("Tailwind CSS from Scratch", "Udemy", "https://www.udemy.com/course/tailwind-css-from-scratch/", "10 hours", "Beginner"),
    "redux": ("Modern React with Redux", "Udemy", "https://www.udemy.com/course/react-redux/", "40 hours", "Intermediate"),

    # Methodologies
    "agile": ("Agile with Atlassian Jira", "Coursera", "https://www.coursera.org/learn/agile-atlassian-jira", "4 weeks", "Beginner"),
    "scrum": ("Agile Development with Scrum", "Coursera", "https://www.coursera.org/learn/agile-development", "4 weeks", "Beginner"),
}


def course_for_skill(skill: str, priority: float, reason: str) -> LearningRecommendation:
    key = skill.lower()
    if key in COURSES:
        title, provider, url, duration, difficulty = COURSES[key]
    else:
        title, provider, url, duration, difficulty = (
            f"Learn {skill}", "Coursera",
            f"https://www.coursera.org/search?query={quote_plus(skill)}",
            "Self-paced", "All levels",
        )
    return LearningRecommendation(skill, title, provider, url, reason, priority, duration, difficulty)


# (title, provider, url, duration, format)
INTERVIEW_RESOURCES = {
    "default_coding": ("Coding Interview Practice", "Pramp", "https://www.pramp.com/", "45 min per session", "Peer mock interview"),
    "default_system_design": ("System Design Interview Prep", "Interviewing.io", "https://interviewing.io/", "60 min per session", "Anonymous mock interview"),
    "default_behavioral": ("Behavioral Interview Prep", "Interviewing.io", "https://interviewing.io/", "30 min per session", "Mock behavioral interview"),
    "leetcode": ("LeetCode Problems", "LeetCode", "https://leetcode.com/problemset/all/", "Self-paced", "Solo coding practice"),
    "hackerrank": ("HackerRank Challenges", "HackerRank", "https://www.hackerrank.com/domains", "Self-paced", "Solo coding practice"),
    "codesignal": ("CodeSignal Practice", "CodeSignal", "https://codesignal.com/", "Self-paced", "Solo coding practice"),
    "educative": ("System Design Courses", "Educative", "https://www.educative.io/courses/grokking-the-system-design-interview", "10 hours", "Guided course"),
    "neetcode": ("NeetCode Roadmap", "NeetCode", "https://neetcode.io/roadmap", "Self-paced", "Curated problem sets"),
    "stratascratch": ("Data Science Interviews", "StrataScratch", "https://www.stratascratch.com/", "Self-paced", "SQL & Python problems"),
    "datalemur": ("SQL Interview Practice", "DataLemur", "https://datalemur.com/", "Self-paced", "SQL case studies"),
    " interviewingio_anon": ("Anonymous Mock Interviews", "Interviewing.io", "https://interviewing.io/", "60 min per session", "Anonymous mock interview"),
    "pramp_peer": ("Peer Mock Interviews", "Pramp", "https://www.pramp.com/", "45 min per session", "Peer mock interview"),
    "candor": ("Salary Negotiation Prep", "Candor", "https://www.candor.co/", "Self-paced", "Negotiation coaching"),
    "levels_fyi": ("Salary & Comp Data", "Levels.fyi", "https://www.levels.fyi/", "Self-paced", "Compensation research"),
    "glassdoor": ("Interview Reviews", "Glassdoor", "https://www.glassdoor.com/Interview/", "Self-paced", "Company interview insights"),
}


def interview_practice_for_skill(skill: str) -> list[InterviewPracticeRecommendation]:
    """Return a list of interview practice resources for the given skill."""
    key = skill.lower()
    results = []

    if key in {"python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "ruby", "php", "swift", "kotlin"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Grind " + skill + " coding problems", "LeetCode",
            "https://leetcode.com/problemset/all/", "Solve " + skill + " problems on LeetCode organized by difficulty and frequency.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Peer mock " + skill + " interviews", "Pramp",
            "https://www.pramp.com/", "Schedule a timed peer mock interview focusing on data structures and algorithms in " + skill + ".",
            "45 min per session", "Peer mock interview",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Practice " + skill + " on HackerRank", "HackerRank",
            "https://www.hackerrank.com/domains", "Complete " + skill + " algorithmic challenges and earn badges.",
            "Self-paced", "Solo practice",
        ))

    elif key in {"sql", "mysql", "postgresql", "mongodb", "redis"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Solve " + skill + " case studies", "DataLemur",
            "https://datalemur.com/", "Work through real-world SQL case studies from top tech companies.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Practice " + skill + " interview questions", "StrataScratch",
            "https://www.stratascratch.com/", "Solve SQL and database questions sourced from actual FAANG interviews.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Peer mock " + skill + " interviews", "Pramp",
            "https://www.pramp.com/", "Practice SQL query problems with a peer and discuss optimal solutions.",
            "30 min per session", "Peer mock interview",
        ))

    elif key in {"aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Grok " + skill + " system design", "Educative",
            "https://www.educative.io/courses/grokking-the-system-design-interview", "Take the Grokking System Design course covering cloud architecture patterns.",
            "10 hours", "Guided course",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Anonymous " + skill + " mock interviews", "Interviewing.io",
            "https://interviewing.io/", "Book an anonymous system design mock interview and practice explaining architecture trade-offs.",
            "60 min per session", "Anonymous mock interview",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Study " + skill + " interview prep", "Educative",
            "https://www.educative.io/courses/grokking-the-system-design-interview", "Complete the " + skill + " specific modules on cloud architecture and infrastructure.",
            "5-8 hours", "Self-paced course",
        ))

    elif key in {"react", "vue", "angular", "next.js", "nextjs", "django", "flask", "fastapi", "spring boot", "node.js", "nodejs"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Mock " + skill + " project interviews", "Interviewing.io",
            "https://interviewing.io/", "Walk through a " + skill + " project and explain design decisions in a mock interview.",
            "45 min per session", "Anonymous mock interview",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Peer code review for " + skill, "Pramp",
            "https://www.pramp.com/", "Practice live coding and code review sessions focused on " + skill + " projects.",
            "45 min per session", "Peer mock interview",
        ))

    elif key in {"machine learning", "deep learning", "tensorflow", "pytorch", "data science"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Solve " + skill + " interview problems", "StrataScratch",
            "https://www.stratascratch.com/", "Solve ML and data science questions sourced from actual tech company interviews.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Practice " + skill + " coding rounds", "LeetCode",
            "https://leetcode.com/problemset/all/", "Focus on LeetCode's ML and algorithm sections for data science roles.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Mock " + skill + " interviews", "Pramp",
            "https://www.pramp.com/", "Practice explaining ML concepts and model selection reasoning with a peer.",
            "45 min per session", "Peer mock interview",
        ))

    elif key in {"tableau", "power bi", "powerbi", "excel", "data analysis", "data analytics"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Practice " + skill + " case interviews", "StrataScratch",
            "https://www.stratascratch.com/", "Work through data analysis case studies and practice presenting findings clearly.",
            "Self-paced", "Solo practice",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Solve " + skill + " SQL problems", "DataLemur",
            "https://datalemur.com/", "Complete SQL case studies that test data analysis and visualization skills.",
            "Self-paced", "Solo practice",
        ))

    elif key in {"agile", "scrum", "kanban"}:
        results.append(InterviewPracticeRecommendation(
            skill, f"Review " + skill + " interview questions", "Glassdoor",
            "https://www.glassdoor.com/Interview/", "Review " + skill + " interview questions on Glassdoor and practice STAR-format answers.",
            "Self-paced", "Self-paced prep",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Study " + skill + " certification prep", "Coursera",
            "https://www.coursera.org/learn/agile-atlassian-jira", "Complete the Agile with Atlassian Jira course to validate your " + skill + " knowledge.",
            "4 weeks", "Guided course",
        ))

    else:
        results.append(InterviewPracticeRecommendation(
            skill, f"Practice explaining " + skill + " in interviews", "Interviewing.io",
            "https://interviewing.io/", "Book a mock interview and prepare concrete project examples using " + skill + ".",
            "30 min per session", "Anonymous mock interview",
        ))
        results.append(InterviewPracticeRecommendation(
            skill, f"Review " + skill + " interview questions", "Glassdoor",
            "https://www.glassdoor.com/Interview/", "Search for " + skill + " interview questions and company reviews on Glassdoor.",
            "Self-paced", "Self-paced prep",
        ))

    return results
