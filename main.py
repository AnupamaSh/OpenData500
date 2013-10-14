#    Sample main.py Tornado file
#    (for Tornado on Heroku)
#
#    Author: Mike Dory | dory.me
#    Created: 11.12.11 | Updated: 06.02.13
#    Contributions by Tedb0t, gregory80
#
# ------------------------------------------

#!/usr/bin/env python
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

#Mongo
from mongoengine import *
import models
import bson
from bson import json_util

# import and define tornado-y things
from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)

#Connect to mongo
connect('db', host=os.environ.get('MONGOLAB_URI'))

# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/submitCompany", SubmitCompanyHandler),
            (r"/edit/([a-zA-Z0-9]{24})", EditCompanyHandler),
            (r"/addData/([a-zA-Z0-9]{24})", SubmitDataHandler),
            (r"/editData/([a-zA-Z0-9]{24})", EditDataHandler),
            (r"/delete/([a-zA-Z0-9]{24})", DeleteCompanyHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Company": CompanyModule},
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


# the main page
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        companies = models.Company.objects()
        self.render(
            "index.html",
            page_title='OpenData500',
            page_heading='Welcome to the OpenData 500',
            companies = companies
        )

class SubmitCompanyHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "submitCompany.html",
            page_title = "Submit a Company",
            page_heading = "Submit a Company"
        )
    def post(self):
        firstName = self.get_argument("firstName", None)
        lastName = self.get_argument("lastName", None)
        url = self.get_argument('url', None)
        companyName = self.get_argument("companyName", None)
        email = self.get_argument("email", None)
        phone = self.get_argument("phone", None)
        ceoFirstName = self.get_argument("ceoFirstName", None)
        ceoLastName = self.get_argument("ceoLastName", None)
        ceoEmail = self.get_argument("ceoEmail", None)
        companyType = self.get_argument("companyType", None)
        if companyType == 'other':
            companyType = self.get_argument('otherCompanyType', None)
        yearFounded = self.get_argument("yearFounded", None)
        fte = self.get_argument("fte", None)
        companyFunction = self.get_argument("companyFunction", None)
        if companyFunction == 'other':
            companyFunction = self.get_argument('otherCompanyFunction', None)
        criticalDataTypes = self.request.arguments['criticalDataTypes']
        criticalDataTypes.append(self.get_argument('otherCriticalDataTypes', None))
        revenueSource = self.request.arguments['revenueSource']
        revenueSource.append(self.get_argument('otherRevenueSource', None))
        sector = self.request.arguments['sector']
        sector.append(self.get_argument('otherSector', None))
        descriptionLong = self.get_argument('descriptionLong', None)
        descriptionShort = self.get_argument('descriptionShort', None)
        socialImpact = self.get_argument('socialImpact', None)
        financialInfo = self.get_argument('financialInfo')
        datasetWishList = self.get_argument('datasetWishList', None)
        companyRec = self.get_argument('companyRec', None)
        conferenceRec = self.get_argument('conferenceRec', None)
        submitter = models.Person(
            firstName = firstName,
            lastName = lastName,
            email = email,
            phone = phone,
            personType = "Submitter",
            datasetWishList = datasetWishList,
            companyRec = companyRec,
            conferenceRec = conferenceRec
        )
        submitter.save()
        ceo = models.Person(
            firstName = ceoFirstName,
            lastName = ceoLastName,
            email = ceoEmail,
            personType = "CEO"
        )
        ceo.save()
        company = models.Company(
            companyName = companyName,
            url = url,
            ceo = ceo,
            yearFounded = yearFounded,
            fte = fte,
            companyType = companyType,
            companyFunction = companyFunction,
            criticalDataTypes = criticalDataTypes,
            revenueSource = revenueSource,
            sector = sector,
            descriptionLong = descriptionLong,
            descriptionShort = descriptionShort,
            socialImpact = socialImpact,
            financialInfo = financialInfo,
            vetted = False
        )
        company.save()
        submitter.submittedCompany = company
        submitter.save()
        id = str(company.id)
        self.redirect("/addData/" + id)

class SubmitDataHandler(tornado.web.RequestHandler):
    def get(self, id):
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        page_heading = "Enter Data Sets for " + company.companyName
        self.render("submitData.html",
            page_title = "Submit Data Sets For Company",
            page_heading = page_heading,
            id = id
        )
    def post(self, id):
        id = self.get_argument('id', None)
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        datasetName = self.get_argument('datasetName', None)
        datasetURL = self.get_argument('datasetURL', None)
        dataType = self.request.arguments['dataType']
        if 'Other' in dataType:
            del dataType[dataType.index('Other')]
            dataType.append(self.get_argument('otherDataType', None))
        ratingSubmitted = self.get_argument('rating', None)
        reason = self.get_argument('reason', None)
        author = company.submitter
        rating = models.Rating(
            author = author,
            rating =ratingSubmitted,
            reason = reason
        )
        dataset = models.Dataset(
            datasetName = datasetName,
            datasetURL = datasetURL,
            dataType = dataType,
            rating = rating
        )
        dataset.usedBy.append(company)
        dataset.save()
        company.datasets.append(dataset)
        company.save()
        self.redirect("/")

class EditCompanyHandler(tornado.web.RequestHandler):
    def get(self, id):
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        page_heading = "Editing " + company.companyName
        page_title = "Editing " + company.companyName
        companyType = ['Public', 'Private', 'Nonprofit']
        companyFunction = ['Consumer Research and/or Marketing', 'Consumer Services', 'Data Management and Analysis', 'Financial/Investment Services', 'Information for Consumers']
        criticalDataTypes = ['Federal Open Data', 'State Open Data', 'City/Local Open Data', 'Private/Proprietary Data Sources']
        revenueSource = ['Advertising', 'Data Management and Analytic Services', 'Database Licensing', 'Lead Generation To Other Businesses', 'Philanthropy', 'Software Licensing', 'Subscriptions', 'User Fees for Web or Mobile Access']
        sectors = ['Agriculture', 'Arts, Entertainment and Recreation' 'Crime', 'Education', 'Energy', 'Environmental', 'Finance', 'Geospatial data/mapping', 'Health and Healthcare', 'Housing/Real Estate', 'Manufacturing', 'Nutrition', 'Scientific Research', 'Social Assistance', 'Trade', 'Transportation', 'Telecom', 'Weather']
        if company is None:
            self.render("404.html", message=id)
        self.render("editCompany.html",
            page_title = page_title,
            page_heading = page_heading,
            company = company,
            companyType = companyType,
            companyFunction = companyFunction,
            criticalDataTypes = criticalDataTypes,
            revenueSource = revenueSource,
            sectors = sectors
        )

    def post(self, id):
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        url = self.get_argument('url', None)
        company.companyName = self.get_argument("companyName", None)
        company.ceo.firstName = self.get_argument("ceoFirstName", None)
        company.ceo.lastName = self.get_argument("ceoLastName", None)
        company.ceo.email = self.get_argument("ceoEmail", None)
        company.companyType = self.get_argument("companyType", None)
        if company.companyType == 'other':
            company.companyType = self.get_argument('otherCompanyType', None)
        company.yearFounded = self.get_argument("yearFounded", None)
        company.fte = self.get_argument("fte", None)
        company.companyFunction = self.get_argument("companyFunction", None)
        if company.companyFunction == 'other':
            company.companyFunction = self.get_argument('otherCompanyFunction', None)
        company.criticalDataTypes = self.request.arguments['criticalDataTypes']
        company.criticalDataTypes.append(self.get_argument('otherCriticalDataTypes', None))
        company.revenueSource = self.request.arguments['revenueSource']
        company.revenueSource.append(self.get_argument('otherRevenueSource', None))
        company.sector = self.request.arguments['sector']
        company.sector.append(self.get_argument('otherSector', None))
        company.descriptionLong = self.get_argument('descriptionLong', None)
        company.descriptionShort = self.get_argument('descriptionShort', None)
        company.socialImpact = self.get_argument('socialImpact', None)
        company.financialInfo = self.get_argument('financialInfo', None)
        if self.get_argument('vetted') == 'True':
            company.vetted = True
        elif self.get_argument('vetted') == 'False':
            company.vetted = False
        company.save()
        self.redirect('/')

class EditDataHandler(tornado.web.RequestHandler):
    def get(self, id):
        dataset = models.Dataset.objects.get(id=bson.objectid.ObjectId(id))
        datatypes = ['Federal Open Data', 'State Open Data', 'City/Local Open Data']
        self.render("editData.html",
            page_title = "Editing Dataset",
            page_heading = "Edit Datasets",
            datatypes = datatypes,
            dataset = datasets
        )
    def post(self, id):
        datasetName = self.get_argument('datasetName', None)
        datasetURL = self.get_argument('datasetURL', None)
        dataType = self.request.arguments['dataType']
        dataType.append(self.get_argument('dataType', None))
        rating = self.get_argument('rating', None)
        reason = self.get_argument('reason', None)
        dataset = models.Dataset(
            datasetName = datasetName,
            datasetURL = datasetURL,
            dataType = dataType,
            rating = rating, 
            reason = reason,
        )
        id = self.get_argument('id', None)
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        dataset.usedBy.append(company)
        dataset.save()
        company.datasets.append(dataset)
        company.save()
        self.redirect("/")


class DeleteCompanyHandler(tornado.web.RequestHandler):
    def get(self, id):
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        company.delete()
        self.redirect('/')


class CompanyModule(tornado.web.UIModule):
    def render(self, company):
        return self.render_string(
            "modules/company.html",
            company=company
        )
    def css_files(self):
        return "/static/css/styles.css"
    def javascript_files(self):
        return "/static/js/script.js"


# RAMMING SPEEEEEEED!
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    # start it up
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()









































