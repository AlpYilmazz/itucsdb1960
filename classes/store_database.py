from classes.sell_item import SellItem
import psycopg2 as dbapi2


class StoreDatabase:
    def __init__(self):
        self.selling = {}
        self.last_sellid = 0

        file = open(r"heroku_db_url.txt", "r")
        self.dsn = file.read()
        #self.dsn = "dbname='postgres' user='postgres' password='postgrepass' host='localhost' port=5432"

        # self.get_all_from_db()

        # normally get selling items from the sql database!

    def get_all_from_db(self, item_name="%", seller_name="%", price_lw=0, price_hi=-1):
        self.selling.clear()

        if item_name != "%":
            item_name = "%" + item_name + "%"

        if seller_name != "%":
            seller_name = "%" + seller_name + "%"

        sql_getAllSellingInfo = """SELECT selling.sellid, item.name, selling.shortD, selling.price, users.name, image.image, count(question.questionid), count(answer.answerid)
                                    FROM selling left join users ON selling.seller = users.studentno
                                                left join item ON selling.itemid = item.itemid
                                                left join image ON selling.imageid = image.imageid
                                                left join question ON selling.sellid = question.sellid
                                                left join answer ON question.questionid = answer.questionid
                                                                AND selling.sellid = answer.sellid
                                    WHERE (item.name LIKE %(item_name)s
                                        AND users.name LIKE %(seller)s
                                        AND selling.price >= %(price_lw)s
                                        AND selling.price <= %(price_hi)s)
                                    GROUP BY selling.sellid, item.name, selling.shortD, selling.price, users.name, image.image
                                    ORDER BY selling.sellid;"""

        sql_getMaxPrice = """SELECT max(price)
                                FROM selling;"""

        with dbapi2.connect(self.dsn) as connection:
            cursor = connection.cursor()

            if price_hi == -1:
                cursor.execute(sql_getMaxPrice)
                maxPrice = cursor.fetchall()
                if len(maxPrice) > 0:
                    price_hi = maxPrice[0][0]

            cursor.execute(sql_getAllSellingInfo, {'item_name': item_name, 'seller': seller_name, 'price_lw': price_lw, 'price_hi': price_hi})
            for row in cursor:
                sellid, item_name, shortD, price, seller_name, image, n_ques, n_ans = row
                self.selling[sellid] = SellItem(sellid, item_name, price, seller_name, n_ques, n_ans, shortD=shortD, image=image)
                self.last_sellid = max(sellid, self.last_sellid)

            cursor.close()

    def add_selling_item(self, sellItem):
        """self.last_sellid += 1
        self.selling[self.last_sellid] = sellItem"""

        itemid = 0
        userid_no = session["userid"]
        imageid = 0

        sql_insertSelling = """INSERT INTO selling (itemid, imageid, seller, shortD, price) VALUES(
                                    %(itemid)s,
                                    %(imageid)s,
                                    %(seller)s,
                                    %(shortD)s,
                                    %(price)s
                                );"""

        # if item_name and image doesnt exist, create
        sql_itemExists = """SELECT item.itemid, item.name
                            FROM item
                            WHERE (item.name = %(item_name)s);"""

        sql_insertItem = """INSERT INTO item (name) VALUES(
                                %(item_name)s
                            );"""

        sql_imageExists = """SELECT image.imageid, image.image
                                FROM image
                                WHERE (image.image = %(image)s);"""

        sql_insertImage = """INSERT INTO image (image) VALUES(
                                %(image)s
                            );"""

        with dbapi2.connect(self.dsn) as connection:
            cursor = connection.cursor()

            cursor.execute(sql_itemExists, {'item_name': sellItem.item_name})
            itemExist = cursor.fetchall()
            if len(itemExist) == 0:
                # create item
                cursor.execute(sql_insertItem, {'item_name': sellItem.item_name})
                cursor.execute(sql_itemExists, {'item_name': sellItem.item_name})
                new_item = cursor.fetchall()
                itemid = new_item[0][0]
            else:
                itemid = itemExist[0][0]

            cursor.execute(sql_imageExists, {'image': sellItem.image})
            imageExist = cursor.fetchall()
            if len(imageExist) == 0:
                # create image
                cursor.execute(sql_insertImage, {'image': sellItem.image})
                cursor.execute(sql_imageExists, {'image': sellItem.image})
                new_image = cursor.fetchall()
                imageid = new_image[0][0]
            else:
                imageid = imageExist[0][0]

            # set userid correctly!

            cursor.execute(sql_insertSelling, {'itemid': itemid, 'imageid': imageid, 'seller': userid_no, 'shortD': sellItem.shortD, 'price': sellItem.price})

            cursor.close()

        self.get_all_from_db()

        # handle sql database!

    def delete_selling_item(self, sellid):
        if sellid in self.selling:
            del self.selling[sellid]

        # handle sql database!

    def get_selling_item(self, sellid):
        sellItem = self.selling.get(sellid)
        if sellItem is None:
            return None
        sellItem_new = SellItem(sellItem.sellid, sellItem.item_name, sellItem.price, sellItem.seller, sellItem.n_questions, sellItem.n_answers, item_info=sellItem.item_info, shortD=sellItem.shortD, image=sellItem.image)
        return sellItem_new

    def get_all_selling_items(self, item_name="%", seller_name="%", price_lw=0, price_hi=-1):
        if item_name == '' or item_name == None:
            item_name = "%"
        if seller_name == '' or seller_name == None:
            seller_name = "%"
        if price_lw == '' or price_lw == None:
            price_lw = 0
        if price_hi == '' or price_hi == None:
            price_hi = -1

        self.get_all_from_db(item_name=item_name, seller_name=seller_name, price_lw=price_lw, price_hi=price_hi)

        sellingItems = []
        for sellid, sellItem in self.selling.items():
            sellItem_new = SellItem(sellItem.sellid, sellItem.item_name, sellItem.price, sellItem.seller, sellItem.n_questions, sellItem.n_answers, item_info=sellItem.item_info, shortD=sellItem.shortD, image=sellItem.image)
            sellingItems.append((sellid, sellItem_new))
        return sellingItems
