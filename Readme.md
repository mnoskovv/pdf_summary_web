# PDF Summary Web

This project is a simple document processing app designed to extract summaries from documents using OpenAI's API. It supports PDF file uploads, processes the content, and generates summaries.

## Installation

### Requirements
- Computer 😁
- Python 3.9+
- Docker
- Docker Compose

### Setup

1. Clone this repository:
```bash
   git clone https://github.com/mnoskovv/pdf_summary_web.git
   cd pdf_summary_web
   cp .env.example .env
```
2. Paste your OPENAI_API_KEY in .env
and run
```bash
    make build && make up
```
3. App is available in http://localhost:8000/

## How to Use

**Basic use**
1. **Select a PDF file**: Choose the PDF document you want to upload by clicking the "Choose File" button.
2. **Upload the file**: After selecting the file, click the "Upload" button to start the process.
3. **Wait for the summary**: The system will process the PDF, extract the content, and generate a summary using OpenAI's API. This may take a few moments.
4. **Enjoy the summary**: Once the process is complete, the summary will appear on the page, ready for you to read.

**Advanced use**
1. **Setup model, temperature and prompt**: You can open http://localhost:8000/admin and login using `admin` `admin` (they are already exists)
2. **Test outputs**: After selecting model preferences, go to main application, click the "Upload" button to start the process.
3. **Monitor ai logs**: Check ai logs in admin panel and debug outputs

That's it! Just sit back and enjoy the automatically generated summary of your document.

## Future improvements
- **Caching**: Cache processed summaries in Memcached to improve performance.
- **Use QUEUE**: Use for example AWS SQS for guarantee that after file sent, even after server is down and up again document will be processed.
- **Error Handling**: Include rate-limiting, retries, and integration with Sentry for error notifications.
- **Scalability**: Ready for future improvements such as splitting the processing between different services (e.g., PDF processing and AI summarization).
- **Metrics**: Integration with Prometheus for application monitoring and metrics collection.
- **Count number tokens**: Count tokens using tiktoken library for large files, and split processing
- **Use Postgres**: Use postgres for the future
- **Bonus**: Can be easily integrated ai chat to discuss summarized document with support context of conversation
