# Deploy the Cafeteria App to Vercel

This guide deploys the Flask application in this repository to Vercel. The repository root is the Vercel project root.

## 1. Prerequisites

You need:

- A GitHub account with this repository pushed to GitHub
- A Vercel account
- A MongoDB Atlas database
- Python 3.13 for local checks, if you want to test before deploying

The repository already contains the Vercel integration files:

- `api/index.py` loads the Flask WSGI app from `preorder_app/wsgi.py`
- `vercel.json` sends all routes to the Python function
- `requirements.txt` installs the dependencies from `preorder_app/requirements.txt`

## 2. Configure MongoDB Atlas

1. Open your MongoDB Atlas project.
2. Create or select a database cluster.
3. Open **Database Access** and create a database user.
4. Open **Network Access** and add an IP access list entry that permits Vercel connections. For a simple first deployment, `0.0.0.0/0` allows connections from any IP, but protect the database with a strong username and password and restrict access further when possible.
5. Select **Connect**, choose **Drivers**, and copy the connection string.
6. Replace the placeholders in the connection string with the database username and password.

Do not commit the MongoDB connection string to the repository.

## 3. Import the project into Vercel

1. Sign in to [Vercel](https://vercel.com/).
2. Select **Add New...** and choose **Project**.
3. Import the GitHub repository containing this project.
4. Leave the **Root Directory** set to the repository root. Do not select `preorder_app` as the root directory because the Vercel function and configuration are at the repository root.
5. Keep the detected framework setting as the default or select **Other** if Vercel asks for a framework.
6. Do not add a build command. This application is served by the Python function in `api/index.py`.
7. Select **Deploy** after adding the environment variables in the next section.

## 4. Add environment variables

In **Project Settings -> Environment Variables**, add these values. Select the environments where each variable should be available, normally **Production**, **Preview**, and **Development**.

| Name | Value | Required |
| --- | --- | --- |
| `MONGO_URI` | MongoDB Atlas connection string | Yes |
| `DB_NAME` | `cafeteria_app`, or your chosen database name | No, defaults to `cafeteria_app` |
| `SECRET_KEY` | Long random private string | Yes for production security |
| `SENDGRID_API_KEY` | SendGrid API key with Mail Send permission | Only for email broadcasts |
| `EMAIL_FROM` | Verified SendGrid sender address | Only for email broadcasts |

Use a different strong `SECRET_KEY` from any local development value. After adding or changing variables, redeploy the project because environment variables are applied to new deployments.

## 5. Deploy

### Using the Vercel dashboard

1. Open the project in Vercel.
2. Select **Deployments**.
3. Select **Redeploy** for the latest commit, or push a new commit to GitHub.
4. Open the deployment URL when the build finishes.

### Using the Vercel CLI

From the repository root:

```bash
npm install -g vercel
vercel login
vercel
```

For a production deployment:

```bash
vercel --prod
```

When prompted, link the command to the existing Vercel project. Keep the project directory as the repository root.

## 6. Verify the deployment

Open the deployment URL and check:

1. The home page loads.
2. User registration works.
3. Login works after registration.
4. Menu items and cart operations work.
5. An order can be created and appears in MongoDB Atlas.
6. Admin routes redirect unauthenticated users to login.
7. Email broadcasts work if SendGrid variables were configured.

If the deployment returns an error, open **Vercel -> Deployments -> deployment -> Functions** and inspect the function logs. The most common startup error is a missing `MONGO_URI` variable.

## 7. Important serverless limitations

Vercel functions do not provide durable local storage. This application currently writes these files locally:

- Uploaded item images under `preorder_app/app/static/uploads`
- Generated invoices under `preorder_app/app/invoices`

Those files may disappear between function instances or deployments. MongoDB data remains persistent, but files that must persist should be moved to object storage such as Vercel Blob, Cloudinary, Amazon S3, or another storage service.

## 8. Updating the application

Push changes to the connected GitHub branch. Vercel automatically creates a Preview deployment for the commit. After testing the Preview URL, merge or deploy the commit to Production.

Keep secrets in Vercel environment variables. Do not place them in `.env` files committed to Git, source code, or client-side templates.
