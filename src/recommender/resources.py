"""Curated, provider-owned resources for common technical skill gaps.

URLs and durations are deliberately stored as data so an API or UI can
render them without hard-coding career advice in a view.  Unknown skills
still receive a useful provider search link rather than being silently
omitted.
"""

from urllib.parse import quote_plus

from .models import InterviewPracticeRecommendation, LearningRecommendation


# (title, provider, url, estimated_duration)
COURSES = {
    # ── Programming Languages ──────────────────────────────────────
    "python": ("Python for Everybody", "Coursera (University of Michigan)", "https://www.coursera.org/specializations/python", "~4 months (20 hrs/week)"),
    "javascript": ("The Complete JavaScript Course", "Udemy (Jonas Schmedtmann)", "https://www.udemy.com/course/the-complete-javascript-course/", "~69 hours"),
    "typescript": ("Understanding TypeScript", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/understanding-typescript/", "~15 hours"),
    "java": ("Java Programming and Software Engineering Fundamentals", "Coursera (Duke University)", "https://www.coursera.org/specializations/java-programming", "~5 months (10 hrs/week)"),
    "go": ("Go: The Complete Developer's Guide", "Udemy (Stephen Grider)", "https://www.udemy.com/course/go-the-complete-developers-guide/", "~24 hours"),
    "golang": ("Go: The Complete Developer's Guide", "Udemy (Stephen Grider)", "https://www.udemy.com/course/go-the-complete-developers-guide/", "~24 hours"),
    "rust": ("Rust Programming", "freeCodeCamp", "https://www.freecodecamp.org/learn/rust/", "~8 hours"),
    "c++": ("C++ For C Programmers", "Coursera (University of California)", "https://www.coursera.org/learn/c-plus-plus-for-c-programmers", "~4 weeks"),
    "c#": ("C# Programming for Unity Game Development", "Coursera (University of Colorado)", "https://www.coursera.org/specializations/c-sharp-programming-unity", "~4 months"),
    "php": ("PHP for Beginners", "Udemy (Danny Smith)", "https://www.udemy.com/course/php-for-complete-beginners-includes-msql-database/", "~6 hours"),
    "ruby": ("The Complete Ruby on Rails Developer Course", "Udemy", "https://www.udemy.com/course/the-complete-ruby-on-rails-developer-course/", "~47 hours"),
    "kotlin": ("Kotlin for Java Developers", "Coursera (JetBrains)", "https://www.coursera.org/learn/kotlin-for-java-developers", "~4 weeks"),
    "swift": ("Developing iOS Apps with Swift", "Coursera (Apple)", "https://www.coursera.org/learn/app-dev-with-swift", "~5 weeks"),
    "scala": ("Functional Programming Principles in Scala", "Coursera (EPFL)", "https://www.coursera.org/learn/progfun1", "~7 weeks"),
    "r": ("R Programming", "Coursera (Johns Hopkins)", "https://www.coursera.org/learn/r-programming", "~4 weeks"),
    "sql": ("SQL for Data Science", "Coursera (UC Davis)", "https://www.coursera.org/learn/sql-for-data-science", "~4 weeks"),
    "bash": ("Linux Command Line Basics", "Udacity", "https://www.udacity.com/course/linux-command-line-basics--ud590", "~5 hours"),
    "perl": ("Learning Perl", "O'Reilly", "https://www.oreilly.com/library/view/learning-perl/9781492094951/", "~4-6 weeks"),
    "matlab": ("MATLAB Onramp", "MathWorks", "https://matlabacademy.mathworks.com/details/matlab-onramp/gettingstarted", "~2 hours"),
    "julia": ("Julia Scientific Programming", "Coursera (University of Cape Town)", "https://www.coursera.org/learn/julia-programming", "~5 weeks"),
    "dart": ("Dart & Flutter - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/complete-flutter-development-bootcamp/", "~39 hours"),

    # ── Web Frameworks ─────────────────────────────────────────────
    "django": ("Django for Everybody", "Coursera (University of Michigan)", "https://www.coursera.org/specializations/django", "~5 months"),
    "fastapi": ("FastAPI - The Complete Course", "Udemy (Eric Roby)", "https://www.udemy.com/course/fastapi-the-complete-course/", "~14 hours"),
    "flask": ("Flask: Develop Web Applications in Python", "Udemy (Eric Roby)", "https://www.udemy.com/course/flask-develop-web-applications-in-python/", "~9 hours"),
    "react": ("The Complete React Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/complete-react-across-hooks-redux-nextjs/", "~48 hours"),
    "vue": ("Vue - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/vuejs-the-complete-guide/", "~37 hours"),
    "angular": ("Angular - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/complete-guide-to-angular-2/", "~37 hours"),
    "express": ("Node.js, Express, MongoDB - The Complete Bootcamp", "Udemy (Jonas Schmedtmann)", "https://www.udemy.com/course/nodejs-express-mongodb-the-complete-bootcamp/", "~40 hours"),
    "spring": ("Spring Framework 6 - Beginner to Guru", "Udemy (Craig Walls)", "https://www.udemy.com/course/spring-framework-6-beginner-to-guru/", "~43 hours"),
    "spring boot": ("Master Spring Boot", "Udemy (Chad Darby)", "https://www.udemy.com/course/spring-boot-masterclass/", "~33 hours"),
    "laravel": ("Laravel: The Ultimate Beginner's Guide", "Udemy", "https://www.udemy.com/course/laravel-ultimate-beginners-guide/", "~11 hours"),
    "rails": ("The Complete Ruby on Rails Developer Course", "Udemy", "https://www.udemy.com/course/the-complete-ruby-on-rails-developer-course/", "~47 hours"),
    "next.js": ("Next.js 14 & React - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/nextjs-react-the-complete-guide/", "~30 hours"),
    "svelte": ("Svelte 4 - The Complete Developer's Guide", "Udemy (Stephen Grider)", "https://www.udemy.com/course/sveltejs-the-complete-guide/", "~12 hours"),
    ".net": (".NET Microservices - Architecture Guide", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/microservices-architecture/", "~16 hours"),
    "node.js": ("Node.js, Express, MongoDB - The Complete Bootcamp", "Udemy (Jonas Schmedtmann)", "https://www.udemy.com/course/nodejs-express-mongodb-the-complete-bootcamp/", "~40 hours"),
    "gin": ("Building Go Web Applications with Gin", "Udemy", "https://www.udemy.com/course/building-go-web-applications-with-gin/", "~8 hours"),

    # ── Cloud Platforms ────────────────────────────────────────────
    "aws": ("AWS Cloud Practitioner Essentials", "AWS Skill Builder", "https://skillbuilder.aws/learn/course/external/view/elearning/aws-cloud-practitioner-essentials", "~6 hours"),
    "gcp": ("Google Cloud Fundamentals: Core Infrastructure", "Coursera (Google Cloud)", "https://www.coursera.org/learn/gcp-fundamentals", "~12 hours"),
    "azure": ("Azure Fundamentals (AZ-900)", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/", "~5 hours"),
    "cloudflare": ("Cloudflare Fundamentals", "Cloudflare Learning Center", "https://developers.cloudflare.com/fundamentals/", "~4 hours"),
    "heroku": ("Heroku Dev Center", "Heroku", "https://devcenter.heroku.com/start", "~2 hours"),
    "digitalocean": ("DigitalOcean Cloud Engineering", "DigitalOcean Tutorials", "https://docs.digitalocean.com/tutorials/", "~6 hours"),

    # ── Databases ──────────────────────────────────────────────────
    "postgresql": ("PostgreSQL for Everybody", "Coursera (University of Michigan)", "https://www.coursera.org/learn/postgresql-for-everybody", "~4 weeks"),
    "mongodb": ("MongoDB for Developers", "MongoDB University", "https://learn.mongodb.com/", "~10 hours"),
    "redis": ("Redis University", "Redis", "https://university.redis.com/", "~6 hours"),
    "elasticsearch": ("Elastic Training", "Elastic", "https://www.elastic.co/training/", "~8 hours"),
    "dynamodb": ("DynamoDB Deep Dive", "AWS Skill Builder", "https://skillbuilder.aws/learn/course/external/view/elearning/dynamodb-deep-dive", "~4 hours"),
    "mysql": ("MySQL for Developers", "Udemy", "https://www.udemy.com/course/mysql-for-developers/", "~10 hours"),
    "graphql": ("GraphQL: The Complete Guide", "Udemy (Stephen Grider)", "https://www.udemy.com/course/graphql-the-complete-guide/", "~27 hours"),
    "prisma": ("Prisma - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/prisma-the-complete-guide/", "~14 hours"),
    "supabase": ("Supabase: The Complete Guide", "Udemy", "https://www.udemy.com/course/supabase-the-complete-guide/", "~8 hours"),
    "firebase": ("Firebase Web Devs", "Firebase Training", "https://firebase.google.com/codelabs/", "~6 hours"),
    "clickhouse": ("ClickHouse Course", "ClickHouse University", "https://university.clickhouse.com/", "~5 hours"),

    # ── AI/ML Tools ────────────────────────────────────────────────
    "tensorflow": ("TensorFlow Developer Certificate", "Coursera (DeepLearning.AI)", "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "~4 months"),
    "pytorch": ("PyTorch for Deep Learning", "freeCodeCamp", "https://www.freecodecamp.org/learn/pytorch-for-deep-learning/", "~25 hours"),
    "scikit-learn": ("Machine Learning with Scikit-Learn", "Coursera (University of Michigan)", "https://www.coursera.org/learn/python-machine-learning", "~4 weeks"),
    "pandas": ("Data Analysis with Pandas", "freeCodeCamp", "https://www.freecodecamp.org/learn/data-analysis-with-python/", "~300 hours (full cert)"),
    "numpy": ("NumPy Course", "freeCodeCamp", "https://www.freecodecamp.org/learn/scientific-computing-with-python/", "~300 hours (full cert)"),
    "opencv": ("Learn OpenCV", "PyImageSearch", "https://pyimagesearch.com/course/", "~10 hours"),
    "langchain": ("LangChain for LLM Application Development", "DeepLearning.AI", "https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/", "~1 hour"),
    "mlflow": ("MLflow Course", "Databricks Academy", "https://www.databricks.com/learn/training/mlflow", "~4 hours"),
    "jupyter": ("Jupyter Notebook Tutorial", "DataCamp", "https://www.datacamp.com/courses/jupyter-notebook-tutorial-for-data-science", "~4 hours"),
    "rag": ("Building RAG Apps with Python", "DeepLearning.AI", "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/", "~1 hour"),
    "openai": ("ChatGPT Prompt Engineering for Developers", "DeepLearning.AI", "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/", "~1 hour"),
    "huggingface": ("Hugging Face Course", "Hugging Face", "https://huggingface.co/learn/nlp-course", "~15 hours"),
    "llm": ("Large Language Model Course", "GitHub (Full Stack LLM)", "https://fullstackdeeplearning.com/llm-bootcamp/", "~8 hours"),

    # ── DevOps & Infrastructure ────────────────────────────────────
    "docker": ("Docker for the Absolute Beginner", "Udemy (Mumshad Mannambeth)", "https://www.udemy.com/course/docker-for-the-absolute-beginner/", "~11 hours"),
    "kubernetes": ("Kubernetes for the Absolute Beginners", "Udemy (Mumshad Mannambeth)", "https://www.udemy.com/course/kubernetes-for-the-absolute-beginners/", "~9 hours"),
    "terraform": ("HashiCorp Terraform Associate Certification", "Udemy (Zeal Vora)", "https://www.udemy.com/course/terraform-beginner-to-advanced/", "~25 hours"),
    "ansible": ("Ansible for the Absolute Beginners", "Udemy (Mumshad Mannambeth)", "https://www.udemy.com/course/ansible-for-the-absolute-beginners/", "~8 hours"),
    "jenkins": ("Jenkins, From Zero To Hero", "Udemy (Mumshad Mannambeth)", "https://www.udemy.com/course/jenkins-from-zero-to-hero/", "~8 hours"),
    "git": ("Git & GitHub Crash Course", "Udemy (Traversy Media)", "https://www.udemy.com/course/git-and-github-crash-course/", "~2 hours"),
    "github": ("GitHub Actions", "GitHub Skills", "https://skills.github.com/", "~4 hours"),
    "gitlab": ("GitLab CI/CD Fundamentals", "GitLab University", "https://university.gitlab.com/", "~6 hours"),
    "ci/cd": ("CI/CD Pipelines Explained", "Udacity", "https://www.udacity.com/course/continuous-integration-continuous-delivery--ud611", "~5 hours"),
    "prometheus": ("Monitoring with Prometheus", "Udemy", "https://www.udemy.com/course/monitoring-with-prometheus/", "~10 hours"),
    "grafana": ("Grafana Fundamentals", "Grafana Labs", "https://grafana.com/tutorials/", "~4 hours"),
    "vault": ("HashiCorp Vault Associate", "Udemy", "https://www.udemy.com/course/hashicorp-vault-certified-associate/", "~12 hours"),
    "pulumi": ("Pulumi Fundamentals", "Pulumi University", "https://www.pulumi.com/docs/get-started/", "~3 hours"),
    "datadog": ("Datadog Fundamentals", "Datadog Learning Center", "https://learn.datadoghq.com/", "~5 hours"),
    "splunk": ("Splunk Fundamentals", "Splunk Education", "https://education.splunk.com/", "~6 hours"),

    # ── Data & Big Data ────────────────────────────────────────────
    "spark": ("Big Data with PySpark", "Udemy (Sundog Education)", "https://www.udemy.com/course/big-data-with-pyspark-and-hadoop/", "~15 hours"),
    "hadoop": ("Hadoop Foundations", "Cloudera", "https://www.cloudera.com/training.html", "~8 hours"),
    "kafka": ("Apache Kafka Fundamentals", "Confluent", "https://developer.confluent.io/learn/", "~6 hours"),
    "airflow": ("Apache Airflow: From Setup to Production", "Udemy", "https://www.udemy.com/course/apache-airflow-from-setup-to-production/", "~14 hours"),
    "dbt": ("dbt Fundamentals", "dbt Learn", "https://courses.getdbt.com/", "~6 hours"),
    "snowflake": ("Snowflake Fundamentals", "Snowflake University", "https://learn.snowflake.com/", "~8 hours"),
    "bigquery": ("Google BigQuery for Data Analysts", "Coursera (Google Cloud)", "https://www.coursera.org/learn/google-bigquery-for-data-analysts", "~12 hours"),
    "databricks": ("Databricks Fundamentals", "Databricks Academy", "https://www.databricks.com/learn", "~6 hours"),
    "airflow": ("Apache Airflow: From Setup to Production", "Udemy", "https://www.udemy.com/course/apache-airflow-from-setup-to-production/", "~14 hours"),
    "looker": ("Looker Fundamentals", "Google Cloud Training", "https://cloud.google.com/training/looker", "~6 hours"),
    "dagster": ("Dagster University", "Dagster", "https://dagster.io/learn", "~4 hours"),
    "flink": ("Apache Flink Course", "Ververica Academy", "https://ververica.com/academy/", "~8 hours"),

    # ── Analytics & Visualisation ──────────────────────────────────
    "tableau": ("Tableau for Beginners", "Udemy", "https://www.udemy.com/course/tableau-for-beginners/", "~6 hours"),
    "power bi": ("Microsoft Power BI Desktop for Business Intelligence", "Udemy (Maven Analytics)", "https://www.udemy.com/course/power-bi-masterclass/", "~10 hours"),
    "excel": ("Excel Skills for Business", "Coursera (Macquarie University)", "https://www.coursera.org/specializations/excel", "~4 months"),
    "matplotlib": ("Data Visualization with Matplotlib", "freeCodeCamp", "https://www.freecodecamp.org/learn/data-analysis-with-python/", "~300 hours (full cert)"),
    "plotly": ("Interactive Data Visualization with Plotly", "Udemy", "https://www.udemy.com/course/interactive-data-visualization-with-plotly/", "~8 hours"),
    "metabase": ("Metabase Training", "Metabase", "https://www.metabase.com/learn/", "~3 hours"),
    "superset": ("Apache Superset Tutorial", "Superset Documentation", "https://superset.apache.org/docs/using-superset/", "~4 hours"),

    # ── Frontend Technologies ──────────────────────────────────────
    "html": ("HTML & CSS Fundamentals", "freeCodeCamp", "https://www.freecodecamp.org/learn/2022/responsive-web-design/", "~300 hours (full cert)"),
    "css": ("CSS - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/css-the-complete-guide-incl-flexbox-grid-sass/", "~26 hours"),
    "sass": ("Sass (Sass Course for Beginners)", "Udemy (Academind)", "https://www.udemy.com/course/sass-course-for-beginners/", "~8 hours"),
    "webpack": ("Webpack: The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/webpack-the-complete-guide/", "~26 hours"),
    "vite": ("Vite - The Lightning-Fast Build Tool", "Udemy", "https://www.udemy.com/course/vite-the-lightning-fast-build-tool/", "~6 hours"),
    "tailwind": ("Tailwind CSS From Scratch", "Udemy (Brad Traversy)", "https://www.udemy.com/course/tailwind-css-from-scratch/", "~11 hours"),
    "redux": ("Redux - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/redux-the-complete-guide/", "~23 hours"),
    "bootstrap": ("Bootstrap 5 - From Scratch", "Udemy (Brad Traversy)", "https://www.udemy.com/course/bootstrap-5-from-scratch/", "~11 hours"),
    "jest": ("JavaScript Testing with Jest", "Udemy", "https://www.udemy.com/course/javascript-testing-with-jest/", "~8 hours"),
    "playwright": ("Playwright: End-to-End Testing for Web Apps", "Udemy", "https://www.udemy.com/course/playwright-end-to-end-testing/", "~10 hours"),
    "cypress": ("Cypress: End-to-End Testing for Frontend Developers", "Udemy", "https://www.udemy.com/course/cypress-end-to-end-testing-for-frontend-developers/", "~8 hours"),
    "jquery": ("jQuery Fundamentals", "Udemy", "https://www.udemy.com/course/jquery-fundamentals/", "~5 hours"),

    # ── Testing & QA ───────────────────────────────────────────────
    "pytest": ("Python Testing with pytest", "Udemy (Brian Okken)", "https://www.udemy.com/course/pytest-python/", "~5 hours"),
    "selenium": ("Selenium WebDriver with Java", "Udemy (Rahul Shetty)", "https://www.udemy.com/course/selenium-webdriver-with-java/", "~30 hours"),
    "postman": ("Postman: The Complete Guide", "Udemy (Valentin Despa)", "https://www.udemy.com/course/postman-the-complete-guide/", "~12 hours"),
    "jmeter": ("Apache JMeter Masterclass", "Udemy", "https://www.udemy.com/course/apache-jmeter-masterclass/", "~14 hours"),
    "k6": ("Load Testing with k6", "Grafana k6 Docs", "https://grafana.com/docs/k6/", "~4 hours"),
    "junit": ("Java Unit Testing with JUnit 5", "Udemy", "https://www.udemy.com/course/java-unit-testing-junit5/", "~7 hours"),

    # ── Architecture & Practices ───────────────────────────────────
    "rest": ("RESTful API Design", "Coursera (University of Michigan)", "https://www.coursera.org/learn/restful-api-design", "~4 weeks"),
    "grpc": ("gRPC: The Complete Guide", "Udemy (Stephen Grider)", "https://www.udemy.com/course/grpc-the-complete-guide/", "~16 hours"),
    "microservices": ("Microservices with Node.js and React", "Udemy (Stephen Grider)", "https://www.udemy.com/course/microservices-with-nodejs-and-react/", "~29 hours"),
    "api": ("RESTful APIs with Flask", "Udemy", "https://www.udemy.com/course/restful-apis-with-flask/", "~6 hours"),
    "serverless": ("Serverless with AWS Lambda", "Udemy", "https://www.udemy.com/course/serverless-architecture/", "~8 hours"),
    "websockets": ("WebSockets with Python", "Udemy", "https://www.udemy.com/course/websockets-with-python/", "~6 hours"),

    # ── Mobile Development ─────────────────────────────────────────
    "react native": ("React Native - The Practical Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/react-native-the-practical-guide/", "~42 hours"),
    "flutter": ("The Complete Flutter Development Bootcamp", "Udemy (Angela Yu)", "https://www.udemy.com/course/flutter-bootcamp-with-dart/", "~42 hours"),
    "swiftui": ("SwiftUI - The Complete Guide", "Udemy (Maximilian Schwarzmuller)", "https://www.udemy.com/course/swiftui-the-complete-guide/", "~27 hours"),
    "jetpack compose": ("Jetpack Compose Essentials", "Udemy", "https://www.udemy.com/course/jetpack-compose-essentials/", "~20 hours"),

    # ── Security ───────────────────────────────────────────────────
    "oauth": ("OAuth 2.0 and OpenID Connect", "Pluralsight", "https://www.pluralsight.com/courses/oauth-2-openid-connect", "~3 hours"),
    "jwt": ("JSON Web Tokens in 8 Minutes", "Udemy", "https://www.udemy.com/course/json-web-tokens-in-8-minutes/", "~1 hour"),
    "owasp": ("OWASP Top 10", "Udemy", "https://www.udemy.com/course/owasp-top-10/", "~6 hours"),
    "penetration testing": ("Complete Ethical Hacking Bootcamp", "Udemy", "https://www.udemy.com/course/complete-ethical-hacking-bootcamp/", "~25 hours"),

    # ── Infrastructure ─────────────────────────────────────────────
    "linux": ("Linux Essentials", "Coursera (IBM)", "https://www.coursera.org/learn/linux-essentials", "~4 weeks"),
    "nginx": ("Nginx Fundamentals", "Udemy", "https://www.udemy.com/course/nginx-fundamentals/", "~7 hours"),
    "apache": ("Apache HTTP Server Administration", "Udemy", "https://www.udemy.com/course/apache-http-server/", "~8 hours"),
}


def course_for_skill(skill: str, priority: float, reason: str) -> LearningRecommendation:
    key = skill.lower()
    if key in COURSES:
        title, provider, url, duration = COURSES[key]
        return LearningRecommendation(skill, title, provider, url, reason, priority, duration=duration)
    return LearningRecommendation(
        skill, f"Learn {skill}", "Coursera",
        f"https://www.coursera.org/search?query={quote_plus(skill)}", reason, priority,
        duration="Self-paced",
    )


# ── Interview Practice Resources ────────────────────────────────────

# Each skill category maps to a list of (title, provider, url, duration, reason)
# so the recommender can offer a variety of prep options.
_INTERVIEW_RESOURCES: dict[str, list[tuple[str, str, str, str, str]]] = {
    # Coding / Algorithm interviews
    "__coding__": [
        ("Grind 75 - Curated LeetCode Problems", "NeetCode", "https://www.techinterviewhandbook.org/grind75", "~2-4 weeks (1-2 problems/day)", "Curated list of 75 most frequently asked LeetCode problems covering arrays, strings, trees, graphs, and DP."),
        ("LeetCode Top 150 Interview Problems", "LeetCode", "https://leetcode.com/studyplan/top-interview-150/", "~4-6 weeks", "Official LeetCode study plan with the top 150 interview problems asked at FAANG companies."),
        ("Blind 75 LeetCode Questions", "NeetCode", "https://neetcode.io/practice", "~3-4 weeks", "Video explanations for each Blind 75 problem with multiple solution approaches."),
        ("HackerRank Interview Preparation Kit", "HackerRank", "https://www.hackerrank.com/domains/algorithms", "~3-5 weeks", "Structured kit covering arrays, strings, sorting, search, and dynamic programming."),
        ("Pramp - Free Peer Mock Interviews", "Pramp", "https://www.pramp.com/", "~1 hour per session", "Practice live coding interviews with peers in a simulated interview environment."),
    ],
    # Cloud / Infrastructure interviews
    "__cloud__": [
        ("AWS Solutions Architect Practice Exams", "Tutorials Dojo", "https://tutorialsdojo.com/courses/aws-solutions-architect-associate-saa-c03/", "~3-4 weeks", "6 practice exams with detailed explanations for AWS SAA-C03 certification."),
        ("Azure Administrator Practice Tests", "Microsoft Learn", "https://learn.microsoft.com/en-us/certifications/exams/az-104/", "~2-3 weeks", "Official Microsoft practice assessment for Azure Administrator AZ-104."),
        ("GCP Professional Cloud Architect", "Coursera (Google Cloud)", "https://www.coursera.org/professional-certificates/cloud-architect-gcp", "~4 weeks", "Hands-on labs and case studies for GCP cloud architecture certification."),
        ("Kubernetes CKAD Practice", "KodeKloud", "https://kodekloud.com/courses/ckad-mock-exams/", "~2 weeks", "Browser-based terminal simulations for the Certified Kubernetes Application Developer exam."),
        ("Terraform Associate Practice", "HashiCorp Learn", "https://developer.hashicorp.com/terraform/tutorials/certification-003", "~1-2 weeks", "Official HashiCorp study guide and practice for Terraform Associate certification."),
    ],
    # System Design interviews
    "__system_design__": [
        ("System Design Interview Prep", "ByteByteGo", "https://bytebytego.com/", "~4-6 weeks", "Visual system design explanations with whiteboard-style diagrams for common interview questions."),
        ("Grokking the System Design Interview", "Educative", "https://www.educative.io/courses/grokking-the-system-design-interview", "~6-8 weeks", "Comprehensive course covering 30+ system design problems with scalability patterns."),
        ("System Design Primer (Open Source)", "GitHub", "https://github.com/donnemartin/system-design-primer", "~4 weeks", "Free, open-source resource with annotated diagrams and flashcards for system design."),
        ("Excalidraw System Design Practice", "Excalidraw", "https://excalidraw.com/", "~1 hour per session", "Free whiteboard tool for practicing system design diagramming and explaining trade-offs."),
    ],
    # Frontend interviews
    "__frontend__": [
        ("Frontend Interview Handbook", "GreatFrontEnd", "https://www.greatfrontend.com/", "~3-4 weeks", "Structured curriculum with 300+ frontend interview questions and mock interviews."),
        ("JavaScript Interview Prep", "LeetCode", "https://leetcode.com/problemset/", "~3-5 weeks", "JavaScript-specific problem set covering closures, prototypes, async/await, and ES6+."),
        ("CSS Layout & Positioning Challenges", "Frontend Mentor", "https://www.frontendmentor.io/", "~2-3 weeks", "Real-world frontend projects to practice CSS Grid, Flexbox, and responsive design."),
        ("React Interview Questions", "DevInterview", "https://devinterview.io/questions/react-js/", "~1-2 weeks", "Curated React interview questions covering hooks, context, performance, and patterns."),
    ],
    # Behavioral / General interviews
    "__behavioral__": [
        ("STAR Method Behavioral Interview Guide", "The Muse", "https://www.themuse.com/advice/star-interview-method", "~1-2 hours", "Learn the STAR framework (Situation, Task, Action, Result) for structured behavioral answers."),
        ("Interviewing.io - Anonymous Mock Interviews", "Interviewing.io", "https://interviewing.io/", "~1 hour per session", "Anonymous mock interviews with engineers from top companies. Pay only if satisfied."),
        ("Big Interview - AI-Powered Mock Interviews", "Big Interview", "https://www.biginterview.com/", "~1-2 hours", "AI-driven mock interview platform with role-specific question banks and feedback."),
        ("Mock Interview Practice", "Pramp", "https://www.pramp.com/", "~1 hour per session", "Free peer-to-peer mock interviews for both technical and behavioral rounds."),
    ],
}

# Skill → category mapping for interview prep routing
_SKILL_INTERVIEW_CATEGORY: dict[str, str] = {
    # Programming Languages → coding
    "python": "__coding__", "java": "__coding__", "javascript": "__coding__",
    "typescript": "__coding__", "c++": "__coding__", "c#": "__coding__",
    "go": "__coding__", "rust": "__coding__", "sql": "__coding__",
    "kotlin": "__coding__", "swift": "__coding__", "scala": "__coding__",
    "ruby": "__coding__", "php": "__coding__",
    # Cloud → cloud
    "aws": "__cloud__", "azure": "__cloud__", "gcp": "__cloud__",
    "docker": "__cloud__", "kubernetes": "__cloud__", "terraform": "__cloud__",
    "ansible": "__cloud__", "jenkins": "__cloud__", "helm": "__cloud__",
    "prometheus": "__cloud__", "grafana": "__cloud__", "vault": "__cloud__",
    "cloudflare": "__cloud__", "digitalocean": "__cloud__",
    # DevOps → cloud
    "ci/cd": "__cloud__", "git": "__cloud__", "github": "__cloud__",
    "gitlab": "__cloud__", "devops": "__cloud__", "nginx": "__cloud__",
    # Data → coding (SQL/Python heavy)
    "spark": "__coding__", "hadoop": "__coding__", "kafka": "__coding__",
    "airflow": "__coding__", "dbt": "__coding__", "snowflake": "__coding__",
    "bigquery": "__coding__", "databricks": "__coding__",
    # Frontend → frontend
    "react": "__frontend__", "vue": "__frontend__", "angular": "__frontend__",
    "svelte": "__frontend__", "next.js": "__frontend__", "html": "__frontend__",
    "css": "__frontend__", "scss": "__frontend__", "tailwind": "__frontend__",
    "redux": "__frontend__", "webpack": "__frontend__", "vite": "__frontend__",
    # AI/ML → coding
    "tensorflow": "__coding__", "pytorch": "__coding__", "scikit-learn": "__coding__",
    "pandas": "__coding__", "numpy": "__coding__",
    # Mobile → coding
    "react native": "__coding__", "flutter": "__coding__",
    "swiftui": "__coding__", "jetpack compose": "__coding__",
}

# Skills that need system design prep (senior-level)
_SYSTEM_DESIGN_SKILLS = {
    "microservices", "rest", "grpc", "api", "serverless", "websockets",
    "kubernetes", "docker", "terraform", "aws", "azure", "gcp",
}


def interview_practice_for_skill(skill: str) -> InterviewPracticeRecommendation:
    key = skill.lower()

    # Determine category
    category = _SKILL_INTERVIEW_CATEGORY.get(key)

    # Senior-level skills also get system design
    if key in _SYSTEM_DESIGN_SKILLS:
        resources = _INTERVIEW_RESOURCES["__system_design__"]
        title, provider, url, duration, reason = resources[0]
        return InterviewPracticeRecommendation(
            skill, f"System design prep for {skill}", provider, url, reason, duration=duration,
        )

    if category:
        resources = _INTERVIEW_RESOURCES[category]
        title, provider, url, duration, reason = resources[0]
        return InterviewPracticeRecommendation(
            skill, f"Practice {skill} interview questions", provider, url, reason, duration=duration,
        )

    # Default: general behavioral prep
    resources = _INTERVIEW_RESOURCES["__behavioral__"]
    title, provider, url, duration, reason = resources[0]
    return InterviewPracticeRecommendation(
        skill, f"Prepare for interviews involving {skill}", provider, url, reason, duration=duration,
    )
