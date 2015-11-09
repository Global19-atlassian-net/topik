import itertools
import os

from topik.fileio._registry import registered_inputs, registered_outputs
from topik.tests import test_data_path

# this function is the primary API for people using any registered functions.
def read_input(source, source_type="auto", content_field='text',
               output_args=None,
               synchronous_wait=0, **kwargs):
    """
    Read data from given source into Topik's internal data structures.

    Parameters
    ----------
    source : str
        input data.  Can be file path, directory, or server address.
    content_field : str
        Which field contains your data to be analyzed.  Hash of this is used as id.
    source_type : str
        "auto" tries to figure out data type of source.  Can be manually specified instead.
        options for manual specification are ['solr', 'elastic', 'json_stream', 'large_json', 'folder']
    output_type : str
        Internal format for handling user data.  Current options are in the registered_outputs dictionary.
        Default is DictionaryCorpus class.  Specify alternatives using string key from dictionary.
    output_args : dict
        Configuration to pass through to output
    synchronous_wait : positive, real number
        Time in seconds to wait for data to finish uploading to output (this happens
        asynchronously.)  Only relevant for some output types ("elastic", not "dictionary")
    kwargs : any other arguments to pass to input parsers

    Returns
    -------
    iterable output object

    >> ids, texts = zip(*list(iter(raw_data)))
    Examples
    --------
    >>> loaded_corpus = read_input(
    ...         '{}/test_data_json_stream.json'.format(test_data_path))
    >>> solution_text = (
    ... u'Transition metal oxides are being considered as the next generation '+
    ... u'materials in field such as electronics and advanced catalysts; '+
    ... u'between them is Tantalum (V) Oxide; however, there are few reports '+
    ... u'for the synthesis of this material at the nanometer size which could '+
    ... u'have unusual properties. Hence, in this work we present the '+
    ... u'synthesis of Ta2O5 nanorods by sol gel method using DNA as structure '+
    ... u'directing agent, the size of the nanorods was of the order of 40 to '+
    ... u'100 nm in diameter and several microns in length; this easy method '+
    ... u'can be useful in the preparation of nanomaterials for electronics, '+
    ... u'biomedical applications as well as catalysts.')
    >>> solution_text == next(loaded_corpus)['abstract']
    True
    """
    json_extensions = [".js", ".json"]
    #if output_args is None:
    #    output_args = {}

    # solr defaults to port 8983
    if (source_type == "auto" and "8983" in source) or source_type == "solr":
        data_iterator = registered_inputs["read_solr"](source, **kwargs)
    # web addresses default to elasticsearch
    elif (source_type == "auto" and "9200" in source) or source_type == "elastic":
        data_iterator = registered_inputs["read_elastic"](source, **kwargs)
    # files must end in .json.  Try json parser first, try large_json parser next.  Fail otherwise.
    elif (source_type == "auto" and os.path.splitext(source)[1] in json_extensions) or source_type == "json_stream":
        try:
            data_iterator = registered_inputs["read_json_stream"](source, **kwargs)
            # tee the iterator and try to get the first element.  If it fails, this is actually a large_json file.
            next(itertools.tee(data_iterator)[0])
            # reset the iterator after this check so that it starts at
            # document 0 rather than document 1
            data_iterator = registered_inputs["read_json_stream"](source, **kwargs)
        except ValueError as e:
            data_iterator = registered_inputs["read_large_json"](source, **kwargs)
    elif source_type == "large_json":
        data_iterator = registered_inputs["read_large_json"](source, **kwargs)
    # folder paths are simple strings that don't end in an extension (.+3-4 characters), or end in a /
    elif (source_type == "auto" and os.path.splitext(source)[1] == "") or source_type == "folder":
        data_iterator = registered_inputs["read_document_folder"](source, content_field=content_field)
    else:
        raise ValueError("Unrecognized source type: {}.  Please either manually specify the type, or convert your input"
                         " to a supported type.".format(source))
    #if "content_field" not in output_args:
    #    output_args["content_field"] = content_field
    return data_iterator
