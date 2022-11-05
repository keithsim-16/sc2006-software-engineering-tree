import requests
import json


class dataGovAPI():

    def getDatasetIDs():
        resourceIDs = []
        listOfDataSets = ["average-retail-prices-of-selected-items-annual",
                          "tax-rates-for-individual-income-tax",
                          "public-transport-utilisation-average-public-transport-ridership"]
        url = "https://data.gov.sg/api/action/"
        for datasetName in listOfDataSets:
            response = requests.get(
                url+"package_show",
                params={"id": datasetName}
            )

            responseJson = json.loads(response.text)
            resourceID = responseJson["result"]["resources"][0]["id"]
            resourceIDs.append(dict([
                ("datasetName", datasetName),
                ("resourceID", resourceID)]))
        return resourceIDs

    def getDatasetID(self, id):
        url = "https://data.gov.sg/api/action/"
        listOfDataSets = ["average-retail-prices-of-selected-items-annual",
                          "tax-rates-for-individual-income-tax",
                          "public-transport-utilisation-average-public-transport-ridership"]
        response = requests.get(
            url+"package_show",
            params={"id": listOfDataSets[id]}
        )
        responseJson = json.loads(response.text)
        resourceID = responseJson["result"]["resources"][0]["id"]
        size = responseJson["result"]["resources"][0]["fields"][0]["total"]
        return resourceID, size

    def getDataset(self, datasetID, limit=0):
        url = "https://data.gov.sg/api/action/"
        response = requests.get(
            url+"datastore_search",
            params={"resource_id": datasetID,
                    "limit": limit}
        )
        return response.json()

    def get(self):
        resourceIDs = self.getDatasetIDs()
        dataset = self.getDataset(resourceIDs[0]["resourceID"])
        return dataset
