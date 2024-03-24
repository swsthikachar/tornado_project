import os
import re
import threading
import tornado.ioloop
import tornado.web
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from mako.lookup import TemplateLookup
import uvicorn
from mako.template import Template
from bson import ObjectId



#connecting the database

conn=MongoClient("mongodb+srv://root:root@cluster001.trln8b7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster001")
db=conn["storeDB"]
collections=db["stores"]
reviews=db["store"]

# Initialize TemplateLookup
mylookup = TemplateLookup(directories="templates")

static_path = os.path.join(os.path.dirname(__file__), "static")

    # Define Tornado application settings
settings = {
        "static_path": static_path
    }
# Define Tornado routes
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        # Render index.html from templates directory
        template = mylookup.get_template("index.html")
        temp=template.render()
        self.finish(temp)

    def post(self):
        print("Received POST request")
        name = self.get_body_argument("name")
        email = self.get_body_argument("email")
        password = self.get_body_argument("password")

        data = {"name": name, "email": email,"password":password}
        print(data)

        exsitinguser=collections.find_one({"email":email})
        if exsitinguser is None:
              try:
                collections.insert_one(data)
                print("Data inserted successfully:", data)
                self.set_cookie("Uemail", email)
              except Exception as e:
                print("Error inserting data:", e)
              self.redirect("/home")
        else:
            self.write(
                "<h1 style='color:red; font-weight:bold;'>this email is already exsist ,<a href='signin'>signin</a> </h1>")
        
class addHandler(tornado.web.RequestHandler):
    def get(self):
        template1 = mylookup.get_template("add.html")
        self.write(template1.render())

    def post(self):
        print("post method called")
        product = self.get_body_argument("prod")
        email = self.get_cookie("Uemail")  # Corrected cookie name
        review = self.get_body_argument("urev")
        print(product)
        if email:
            data1 = {"product": product, "email": email, "review": review}
            try:
                reviews.insert_one(data1)
                self.redirect("/add")
            except Exception as e:
                print("Error inserting data:", e)
                self.write("Failed to insert data")
        else:
            self.write("User email not found in cookies")  # Handle case when email not found



class ManageHandler(tornado.web.RequestHandler):
    def get(self):
        template2=mylookup.get_template("manage.html")
        Uemail=self.get_cookie("Uemail")
        uitems=reviews.find({"email":Uemail})
        self.write(template2.render(uitems=uitems))


class signinHandler(tornado.web.RequestHandler):
    def get(self):
        template3=mylookup.get_template("signin.html")
        self.write(template3.render())

    def post(self):
        useremail=self.get_body_argument("USemail")
        userpass=self.get_body_argument("USpassword")
        uservalidate=collections.find_one({"email":useremail,"password":userpass})
        if uservalidate is not None:
            self.set_cookie("Uemail", useremail)
            print("succesfull")
            self.redirect("/home")
        else:
            self.write("access not possible")
            self.redirect("/")

class homeHandler(tornado.web.RequestHandler):
     def get(self):
        hometemplate = mylookup.get_template("home.html")
        user_email = self.get_cookie("Uemail")
        
        if user_email:
            item = collections.find_one({"email": user_email})
            if item:
                feedback = reviews.find()
                self.finish(hometemplate.render(item=item,feedback=feedback))
            else:
                # Handle case when user email is not found in the database
                self.write("User not found.")
        else:
            # Handle case when user email is not found in the cookie
            self.write("User email not found in the cookie.")

class DeleteHandler(tornado.web.RequestHandler):
    def post(self):
        item_id=self.get_body_argument('id')
        filter = {"_id": ObjectId(item_id)}
        # Use the filter parameter to specify the document to delete
        result = reviews.find_one_and_delete(filter)
        if result:
            print("Document deleted successfully")
            self.redirect("/manage")
        else:
            print("Document not found or failed to delete")

class modifyHandler(tornado.web.RequestHandler):
    def post(self):
        item_id = self.get_body_argument('id')
        new_rev = self.get_body_argument('modify')
        filter_query = {"_id": ObjectId(item_id)}
        update_operation = {"$set": {"review": new_rev}}
        result = reviews.find_one_and_update(filter_query, update_operation)
        if result:
            print("Modification successful")
            self.redirect("/manage")
        else:
            print("Modification failed")
            self.redirect("/manage")
class logoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("Uemail")
        self.redirect("/")
# Initialize Tornado application
def make_app():
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/add", addHandler),
        (r"/manage", ManageHandler),
        (r"/signin", signinHandler),
        (r"/home", homeHandler),
        (r"/delete", DeleteHandler),
        (r"/modify",modifyHandler),
        (r"/logout",logoutHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
], cookie_secret="your_secret_key", debug=True, autoreload=True)

# Run Tornado server
if __name__ == "__main__":
    tornado_app=make_app()
    tornado_app.listen(8881)
    print("Tornado server is listening")
    tornado.ioloop.IOLoop.current().start()