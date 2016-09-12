# -*- coding: utf-8 -*-
"""Main PyWeed module. Contains WeedFS class

.. moduleauthor:: Łukasz Bołdys
"""

import json
import os
import random
from collections import namedtuple

from .utils import (
    get_data,
    get_raw_data,
    post_file,
    delete_data,
    head
)

from .exceptions import BadFidFormat


class WeedFS(object):
    master_addr = "localhost"
    master_port = 9333

    def __init__(self, master_addr='localhost', master_port=9333):
        '''Creates WeedFS instance.

        Args:
            **master_addr**: Address of weed-fs master server (default: localhost)

            **master_port**: Weed-fs master server port (default: 9333)

        Returns:
            WeedFS instance.
        '''
        self.master_addr = master_addr
        self.master_port = master_port

    def __repr__(self):
        return "<{0} {1}:{2}>".format(
            self.__class__.__name__,
            self.master_addr,
            self.master_port
        )

    def get_file(self, fid):
        """Get file from WeedFS.

        Returns file content. May be problematic for large files as content is
        stored in memory.

        Args:
            **fid**: File identifier <volume_id>,<file_name_hash>

        Returns:
            Content of the file with provided fid or None if file doesn't exist
            on the server

        .. versionadded:: 0.3.1
        """
        url = self.get_file_url(fid)
        return get_raw_data(url)

    def get_file_url(self, fid):
        """
        Get url for the file

        :param string fid: File ID
        :rtype: string
        """
        try:
            volume_id, rest = fid.strip().split(",")
        except ValueError:
            raise BadFidFormat("fid must be in format: <volume_id>,<file_name_hash>")
        file_location = self.get_file_location(volume_id)
        url = "http://{public_url}/{fid}".format(public_url=file_location.public_url, fid=fid)
        return url

    def get_file_location(self, volume_id):
        """
        Get location for the file,
        WeedFS volume is choosed randomly

        :param integer volume_id: volume_id
        :rtype: namedtuple `FileLocation` `{"public_url":"", "url":""}`
        """
        url = "http://{master_addr}:{master_port}/dir/lookup?volumeId={volume_id}".format(
            master_addr=self.master_addr,
            master_port=self.master_port,
            volume_id=volume_id)
        data = json.loads(get_data(url))
        _file_location = random.choice(data['locations'])
        FileLocation = namedtuple('FileLocation', "public_url url")
        return FileLocation(_file_location['publicUrl'], _file_location['url'])

    def get_file_size(self, fid):
        """
        Gets size of uploaded file
        Or None if file doesn't exist.

        Args:
            **fid**: File identifier <volume_id>,<file_name_hash>

        Returns:
            Int or None
        """
        url = self.get_file_url(fid)
        res = head(url)
        if res is not None:
            size = res.headers.get("content-length", None)
            if size is not None:
                return int(size)
        return None

    def file_exists(self, fid):
        """Checks if file with provided fid exists

        Args:
            **fid**: File identifier <volume_id>,<file_name_hash>

        Returns:
            True if file exists. False if not.
        """
        res = self.get_file_size(fid)
        if res is not None:
            return True
        return False

    def delete_file(self, fid):
        """
        Delete file from WeedFS

        :param string fid: File ID
        """
        url = self.get_file_url(fid)
        return delete_data(url)

    def upload_file(self, path=None, stream=None, name=None, **kwargs):
        '''
        Uploads file to WeedFS

        I takes either path or stream and name and upload it
        to WeedFS server.

        Returns fid of the uploaded file.

        :param string path:
        :param string stream:
        :param string name:
        :rtype: string or None

        '''
        url = "http://{master_addr}:{master_port}/dir/assign".format(
            master_addr=self.master_addr,
            master_port=self.master_port)
        data = json.loads(get_data(url))
        if data.get("error") is not None:
            return None
        post_url = "http://{publicUrl}/{fid}".format(**data)

        if path is not None:
            filename = os.path.basename(path)
            with open(path, "rb") as file_stream:
                res = post_file(post_url, filename, file_stream)
        # we have file like object and filename
        elif stream is not None and name is not None:
            res = post_file(post_url, name, stream)
        else:
            raise ValueError("If `path` is None then *both* `stream` and `name` must not be None ")
        response_data = json.loads(res)
        if "size" in response_data:
            return {'fid':data.get('fid'),'size':response_data.get('size')}
        return None

    def vacuum(self, threshold=0.3):
        '''
        Force garbage collection

        :param float threshold (optional): The threshold is optional, and will not change the default threshold.
        :rtype: boolean

        '''
        url = "http://{master_addr}:{master_port}/vol/vacuum?garbageThreshold={threshold}".format(
            master_addr=self.master_addr,
            master_port=self.master_port,
            threshold=threshold)
        res = get_data(url)
        if res is not None:
            return True
        return False

    @property
    def version(self):
        '''
        Returns Weed-FS master version

        :rtype: string
        '''
        url = "http://{master_addr}:{master_port}/dir/status".format(
            master_addr=self.master_addr,
            master_port=self.master_port)
        data = get_data(url)
        response_data = json.loads(data)
        return response_data.get("Version")


if __name__ == "__main__":
    pass
