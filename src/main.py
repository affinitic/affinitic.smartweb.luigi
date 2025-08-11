# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urljoin

import copy
import json
import luigi
import os.path


def remove_sufixe(path):
    if "@@images" in path:
        return path.split("/@@images")[0]

    if path.endswith("/image"):
        return path[:-6]

    if path.endswith("/image/"):
        return path[:-7]

    if path.endswith("/image_large") or path.endswith("/image_thumb"):
        return path[:-12]

    if path.endswith("/image_mini"):
        return path[:-11]

    if path.endswith("/image_preview"):
        return path[:-14]

    return path


def change_prefixe(path, url_absolute=None):
    if url_absolute and path.startswith(url_absolute):
        return path.replace(url_absolute, "http://localhost:8080/Plone/fr")
    return path


def check_url(path):
    if path.startswith("http://localhost:8080/Plone/images"):
        return path.replace(
            "http://localhost:8080/Plone/images",
            "http://localhost:8080/Plone/fr/images",
        )

    return path


def tarverse_id(path, id, url_absolute):
    if id.startswith("fr/images"):
        return os.path.join("http://localhost:8080/Plone", remove_sufixe(id))

    if id.startswith("../afbeeldingen"):
        return os.path.join("http://localhost:8080/Plone/nl", remove_sufixe(id[3:]))

    if id.startswith("http") or id.startswith("https"):
        return remove_sufixe(change_prefixe(id, url_absolute))
    traverse_id = remove_sufixe(change_prefixe(id, url_absolute))

    url_resolve = check_url(urljoin(path, traverse_id))
    return url_resolve


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except:
        return default


def tag_visible(element):
    if (
        element.parent.name in ["style", "script", "head", "title", "meta"]
        or element == "\n"
    ):
        return False
    if isinstance(element, Comment):
        return False
    return True


def check_if_text_present(html):
    html_soup = BeautifulSoup(html)
    texts = html_soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return "".join(t.strip() for t in visible_texts) != ""


class Start(luigi.WrapperTask):
    path = luigi.Parameter()

    def requires(self):
        yield HandleDocument(path=self.path)
        yield HandleImage(path=self.path)


class Document(luigi.ExternalTask):
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"{self.path}/in/Document.json")


class News(luigi.ExternalTask):
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"{self.path}/in/News Item.json")


class Event(luigi.ExternalTask):
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"{self.path}/in/Event.json")


class Image(luigi.ExternalTask):
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"{self.path}/in/Image.json")


class GenerateListOfImageId(luigi.Task):
    path = luigi.Parameter()

    def requires(self):
        return Image(path=self.path)

    def output(self):
        return luigi.LocalTarget(f"{self.path}/temp/ImageID.json")

    def run(self):
        json_output = []

        with self.input().open("r") as image:
            image_json = json.loads(image.read())

        for image in image_json:
            json_output.append({"@id": image.get("@id"), "id": image.get("id")})

        with self.output().open("w") as outfile:
            outfile.write(json.dumps(json_output, indent=4))


class HandleDocument(luigi.Task):
    path = luigi.Parameter()
    url_absolute = luigi.Parameter(default=None)

    list_image = []

    def requires(self):
        return {
            "doc": Document(path=self.path),
            "news": News(path=self.path),
            "event": Event(path=self.path),
            "image": GenerateListOfImageId(path=self.path),
        }

    def output(self):
        print("--------------- HandleDocument.output ---------------")
        return {
            "doc": luigi.LocalTarget(f"{self.path}/out/Document_luigi.json"),
            "news": luigi.LocalTarget(f"{self.path}/out/News Item_luigi.json"),
            "event": luigi.LocalTarget(f"{self.path}/out/Event_luigi.json"),
            "list": luigi.LocalTarget(f"{self.path}/temp/list_image.json"),
        }

    def _get_image_id(self, path):
        with self.input()["image"].open("r") as image:
            image_json = json.loads(image.read())

        result = [
            {"id": image.get("id", path), "path": image.get("@id")}
            for image in image_json
            if path in image.get("@id", "")
        ]

        if len(result) > 0:
            return result

    def _recursive_search_image_id(self, id):
        # print("start searching")
        id_parts = id.split("/")
        count = 1
        result = []
        while len(result) != 1:
            if count > len(id_parts):
                # print("reach end of search string")
                return None
            # print(f"search on {'/'.join(id_parts[-count:])}")
            result = self._get_image_id("/".join(id_parts[-count:]))
            if not result:
                # print("Not found")
                return None
            # print(f"found {len(result)} result")
            count = count + 1

        return result

    def _add_subfolder_in_path(self, path, subfolder, position=-1):
        path_split = path.split("/")
        path_split.insert(position, subfolder)
        return "/".join(path_split)

    def _divide_html_img(self, html, path, type, result=[]):
        # todo: remove parent node from image
        img = html.img
        if not img:
            if html.prettify() != "" and check_if_text_present(html.prettify()):
                result.append({"type": "text", "data": html.prettify()})
            return result

        html_list = html.prettify().split(img.prettify())

        if html_list[0] != "" and check_if_text_present(html_list[0]):
            result.append({"type": "text", "data": html_list[0]})

        image_id = tarverse_id(path, img["src"], self.url_absolute)

        id_from_image = self._get_image_id(image_id)

        if not id_from_image:
            print(f"Image {image_id} not found")
            id_from_image = self._recursive_search_image_id(image_id)

        if type == "Event":
            path = self._add_subfolder_in_path(path, "events")

        if type == "News Item":
            path = self._add_subfolder_in_path(path, "news")

        if id_from_image:
            result.append(
                {
                    "type": "image",
                    "id": safe_list_get(id_from_image, 0, {}).get("id", None),
                }
            )
            self.list_image.append(
                {
                    "image": safe_list_get(id_from_image, 0, {}).get("path", None),
                    "doc": os.path.join(
                        path, safe_list_get(id_from_image, 0, {}).get("id", None)
                    ),
                }
            )

        return self._divide_html_img(BeautifulSoup(html_list[1]), path, type, result)

    def _execute(self, id):

        json_output = []

        with self.input()[id].open("r") as doc:
            doc_json = json.loads(doc.read())

        for count, document in enumerate(doc_json):
            # print(f"{count}/{len(doc_json)} - Start Analyze Document : {document.get('@id','No @id found')}")
            text = document.get("text", None)
            if not text:
                json_output.append(document)
                continue
            soup = BeautifulSoup(text.get("data"))
            result = self._divide_html_img(soup, document["@id"], document["@type"], [])
            document["section_content"] = result
            json_output.append(document)

        print("--------------- HandleDocument.run write ---------------")
        with self.output()[id].open("w") as outfile:
            outfile.write(json.dumps(json_output, indent=4))

    def run(self):
        print("--------------- HandleDocument.run start ---------------")
        for page in ["doc", "news", "event"]:
            self._execute(page)

        # print("----------------------------")
        print("--------------- HandleDocument.run call HandleImage ---------------")
        with self.output()["list"].open("w") as outfile:
            outfile.write(json.dumps(self.list_image, indent=4))
        # yield HandleImage(image_list_id=self.list_image)


class HandleImage(luigi.Task):
    path = luigi.Parameter()

    json_output = []

    def run(self):
        print("--------------- HandleImage.run start ---------------")
        with self.input()["image"].open("r") as image:
            image_json = json.loads(image.read())

        with self.input()["doc"]["list"].open("r") as list:
            image_list_id = json.loads(list.read())

        for count, image in enumerate(image_json):
            # print(f"{count}/{len(image_json)} - Start Analyze Image : {image.get('@id','No @id found')}")
            results = [id for id in image_list_id if id["image"] == image["@id"]]

            for result in results:
                copy_image = copy.deepcopy(image)
                copy_image["section_image"] = result["doc"]
                self.json_output.append(copy_image)

        print("--------------- HandleImage.run write ---------------")
        with self.output().open("w") as outfile:
            outfile.write(json.dumps(self.json_output, indent=4))

    def output(self):
        print("--------------- HandleImage.output ---------------")
        return luigi.LocalTarget(f"{self.path}/out/Image_luigi.json")

    def requires(self):
        return {"image": Image(path=self.path), "doc": HandleDocument(path=self.path)}
