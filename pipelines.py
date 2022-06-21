from itemadapter import ItemAdapter


class UpshelfTestPipeline:
    def process_item(self, item, spider):
        item['description'] = "".join(item.get('description'))
        item['highlights'] = "".join(item.get('highlights'))
        item['specifications'] = "".join(item.get('specifications'))
        return item
