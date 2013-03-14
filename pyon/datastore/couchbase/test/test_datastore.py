from pyon.datastore.couchbase.datastore import CouchbaseDataStore
from pyon.datastore.couchdb.couchdb_datastore import CouchDB_DataStore
from pyon.util.int_test import IonIntegrationTestCase
from nose.plugins.attrib import attr
from pyon.util.log import log
from pyon.core.bootstrap import CFG
from couchbase.client import Couchbase, Bucket
from pyon.public import IonObject, RT, log
from pyon.core.exception import BadRequest, Conflict, NotFound, ServerError
from time import clock, time
from pyon.ion.resource import RT, PRED, LCS
from pyon.datastore.datastore import DataStore
import time
import interface
from unittest import skip
import pprint
from interface.objects import AttachmentType

OWNER_OF = "XOWNER_OF"
HAS_A = "XHAS_A"
BASED_ON = "XBASED_ON"

database_name = "testing"

@attr('UNIT', group='datastore')
class TestCouchbase(IonIntegrationTestCase):

    def setUp(self):
        log.debug("cfg %s", repr(CFG['server'].keys()))
        self.hostname=CFG['server']['couchbase']['host']
        self.username=CFG['server']['couchbase']['username']
        self.password=CFG['server']['couchbase']['password']
        self.resources = {}

        self.datastore_name = database_name
        self.ds = CouchbaseDataStore(datastore_name=self.datastore_name, profile=DataStore.DS_PROFILE.RESOURCES)
        self._delete_and_create_datastore()

    def _create_resource(self, restype, name, *args, **kwargs):
        res_obj = IonObject(restype, dict(name=name, **kwargs))
        res_obj_res = self.ds.create(res_obj)
        res_obj._id = res_obj_res[0]
        self.resources[name] = res_obj
        return res_obj_res[0]

    def _delete_and_create_datastore(self):
        try :
            self.ds.delete_datastore()
        except NotFound:
            pass
        except ServerError:
            pass

        self.ds.create_datastore()

    #@skip("should not be skipped")
    def test_mult(self):
        o1 = IonObject("Dataset", name="One more")
        o2 = IonObject("Dataset", name="Another one")
        res =self.ds.create_mult((o1, o2))

        self.ds._update_views()
        counts = self.ds.list_objects()
        self.assertTrue(len(counts) == 2)
        self.assertTrue(len(res) == 2)

        ids = [ id for _, id, _ in res]
        objs = self.ds.read_mult(ids)
        names = [obj.name for obj in objs]
        self.assertIn(o1.name, names)
        self.assertIn(o2.name, names)

        self.ds.delete_doc_mult(ids)
        with self.assertRaises(NotFound):
            self.ds.read(ids[0])
        with self.assertRaises(NotFound):
            self.ds.read(ids[1])
        with self.assertRaises(NotFound):
            self.ds.read_mult(ids)

    def _petty_print(self, string):
        print "\n\n--------------------------------"
        print pprint.pformat(string)
        print "--------------------------------\n\n"

    #@skip("should not be skipped")
    def test_couchbase_crud_operation (self):

        self.ds._update_views()

        ds, ds_name = self.ds._get_datastore(self.datastore_name)
        self.assertIsInstance(ds, Bucket)

        timer = IonObject("IntervalTimer", {"start_time": "111", "interval": 3, "end_time": "0"})

        # Create
        id, rev = self.ds.create(timer)

        # Read and verify create
        obj = self.ds.read(id)
        self.assertTrue(type(obj)==type(timer), "Types don't match %s : %s" %(type(obj), type(timer)))
        self.assertEqual(obj.start_time, timer.start_time)

        # Update
        updated_data = "2222"
        obj.start_time = updated_data
        id2 , rev2 = self.ds.update(obj)

        # Verify update
        self.assertEqual(id, id2)
        obj2 = self.ds.read(id2)
        self.assertEqual(obj2.start_time, updated_data)

        # Update not-existing object
        temp = IonObject("IntervalTimer", {"start_time": "111", "interval": 3, "end_time": "0"})
        temp._id = "233"
        with self.assertRaises(NotFound):
            self.ds.update(temp)

        # Delete
        self.ds.delete(obj)

        # Verify delete
        with self.assertRaises(NotFound):
            self.ds.delete(obj)
        with self.assertRaises(NotFound):
            self.ds.delete(obj2)
        with self.assertRaises(NotFound):
            self.ds.read(id)
        # Delete

    def test_attachment(self):
        self.ds._update_views()

        # Create an Ion object with default values set (if any)
        data_set = IonObject('Dataset')
        self.assertTrue(isinstance(data_set, interface.objects.Dataset))

        # Assign values to object fields
        data_set.description = "Real-time water data for Choptank River near Greensboro, MD"

        # Write Dataset object"
        write_tuple_1 = self.ds.create(data_set)

        # Save off the object UUID
        data_set_uuid = write_tuple_1[0]

        # Read back the HEAD version of the object
        data_set_read_obj = self.ds.read(data_set_uuid)

        # Update Dataset's Description field and write
        data_set_read_obj.description = "Updated Description"
        write_tuple_2 = self.ds.update(data_set_read_obj)


        # test attachment related stuff
        # create attachment
        ds_id_and_rev = {}
        attachment_name = 'resource.attachment'
        attachment_name2 = 'resource.attachment2'
        ds_id_and_rev['_id'] = write_tuple_2[0]
        ds_id_and_rev['_rev'] = write_tuple_2[1]
        data = "\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x03\x00\x00\x00(-\x0fS\x00\x00\x00\x03sBIT\x08\x08\x08\xdb\xe1O\xe0\x00\x00\x00~PLTEf3\x00\xfc\xf7\xe0\xee\xcc\x00\xd3\xa0\x00\xcc\x99\x00\xec\xcdc\x9fl\x00\xdd\xb2\x00\xff\xff\xff|I\x00\xf9\xdb\x00\xdd\xb5\x19\xd9\xad\x10\xb6\x83\x00\xf8\xd6\x00\xf2\xc5\x00\xd8\xab\x00n;\x00\xff\xcc\x00\xd6\xa4\t\xeb\xb8\x00\x83Q\x00\xadz\x00\xff\xde\x00\xff\xd6\x00\xd6\xa3\x00\xdf\xaf\x00\xde\xad\x10\xbc\x8e\x00\xec\xbe\x00\xec\xd4d\xff\xe3\x00tA\x00\xf6\xc4\x00\xf6\xce\x00\xa5u\x00\xde\xa5\x00\xf7\xbd\x00\xd6\xad\x08\xdd\xaf\x19\x8cR\x00\xea\xb7\x00\xee\xe9\xdf\xc5\x00\x00\x00\tpHYs\x00\x00\n\xf0\x00\x00\n\xf0\x01B\xac4\x98\x00\x00\x00\x1ctEXtSoftware\x00Adobe Fireworks CS4\x06\xb2\xd3\xa0\x00\x00\x00\x15tEXtCreation Time\x0029/4/09Oq\xfdE\x00\x00\x00\xadIDAT\x18\x95M\x8f\x8d\x0e\x820\x0c\x84;ZdC~f\x07\xb2\x11D\x86\x89\xe8\xfb\xbf\xa0+h\xe2\x97\\\xd2^\x93\xb6\x07:1\x9f)q\x9e\xa5\x06\xad\xd5\x13\x8b\xac,\xb3\x02\x9d\x12C\xa1-\xef;M\x08*\x19\xce\x0e?\x1a\xeb4\xcc\xd4\x0c\x831\x87V\xca\xa1\x1a\xd3\x08@\xe4\xbd\xb7\x15P;\xc8\xd4{\x91\xbf\x11\x90\xffg\xdd\x8di\xfa\xb6\x0bs2Z\xff\xe8yg2\xdc\x11T\x96\xc7\x05\xa5\xef\x96+\xa7\xa59E\xae\xe1\x84cm^1\xa6\xb3\xda\x85\xc8\xd8/\x17se\x0eN^'\x8c\xc7\x8e\x88\xa8\xf6p\x8e\xc2;\xc6.\xd0\x11.\x91o\x12\x7f\xcb\xa5\xfe\x00\x89]\x10:\xf5\x00\x0e\xbf\x00\x00\x00\x00IEND\xaeB`\x82"
        some_text = "SOME TEXT"

        data2 = data + data

        # create attachment with no data
        with self.assertRaises(BadRequest):
            self.ds.create_attachment(doc=ds_id_and_rev, data=None, attachment_name=attachment_name, content_type=None, datastore_name="")

        # create attachment with no attachment
        with self.assertRaises(BadRequest):
            self.ds.create_attachment(doc=ds_id_and_rev, data=data, attachment_name=None, content_type=None, datastore_name="")

        #create attachment by passing a doc parameter
        self.ds.create_attachment(doc=ds_id_and_rev, data=data, attachment_name=attachment_name, content_type=None, datastore_name="")
        # One is not enough. Add another attachment
        self.ds.create_attachment(doc=ds_id_and_rev, data=data2, attachment_name=attachment_name2, content_type=None, datastore_name="")

        # list attachment
        attachments = self.ds.list_attachments(doc=ds_id_and_rev)
        self.assertEqual(len(attachments), 2)

        content_read = self.ds.read_attachment(doc=ds_id_and_rev, attachment_name=attachment_name, datastore_name="")
        self.assertEquals(data, content_read)

        content_read2 = self.ds.read_attachment(doc=ds_id_and_rev, attachment_name=attachment_name2, datastore_name="")
        self.assertEquals(data2, content_read2)
        self.assertNotEqual(content_read, content_read2)

        # create attachment with existing name
        with self.assertRaises(BadRequest):
            self.ds.create_attachment(doc=ds_id_and_rev, data=data, attachment_name=attachment_name, content_type=None, datastore_name="")

        # Read wrong attachment name
        with self.assertRaises(NotFound):
            self.ds.read_attachment(doc=ds_id_and_rev, attachment_name="no_name_", datastore_name="")

        # update attachment by passing a doc parameter that is a dictionary containing _id elements
        self.ds.update_attachment(ds_id_and_rev, attachment_name, data=some_text)

        # read the attachment passing only the doc _id and verify that content has changed
        content_read = self.ds.read_attachment(doc=ds_id_and_rev['_id'], attachment_name=attachment_name, datastore_name="")
        self.assertNotEquals(data, content_read)
        self.assertEquals(some_text, content_read)

        # delete attachment by passing a doc parameter that is a dictionary containing _rev
        # and _id elements
        self.ds.delete_attachment(doc=ds_id_and_rev, attachment_name=attachment_name)

        # Read attachment and verify it been deleted
        with self.assertRaises(NotFound):
            self.ds.read_attachment(doc=ds_id_and_rev, attachment_name=attachment_name)

        # Make sure the second attachment hasn't been deleted
        content_read2 = self.ds.read_attachment(doc=ds_id_and_rev, attachment_name=attachment_name2)
        self.assertEquals(data2, content_read2)

        with self.assertRaises(NotFound):
            self.ds.delete_attachment(doc=ds_id_and_rev['_id'], attachment_name='no_such_file')

        with self.assertRaises(NotFound):
            self.ds.delete_attachment('bad_id_really_bad', attachment_name='no_such_file')

        #create attachment by passing a doc parameter that is string indicating _id
        self.ds.create_attachment(doc=ds_id_and_rev['_id'], data=data, attachment_name=attachment_name, content_type=None, datastore_name="")

        # read attachment by passing a doc parameter that is a string indicating _id
        # and verify that the content read is same as the content put in
        content_read = self.ds.read_attachment(doc=ds_id_and_rev['_id'], attachment_name=attachment_name, datastore_name="")
        self.assertEquals(data, content_read)

        # update attachment by passing a doc parameter that is a string indicating _id
        self.ds.update_attachment(ds_id_and_rev['_id'], attachment_name, data=some_text)


        # create another attachment and
        # list attachments by passing a doc parameter that is a dictionary
        # containing _rev and _id elements
        self.ds.create_attachment(doc=ds_id_and_rev['_id'], data=data,
            attachment_name=attachment_name+"_01", content_type=None,
            datastore_name="")
        _attachments = self.ds.list_attachments(doc=ds_id_and_rev)

        #refer to a previous version of the document
        updated_ds_id_and_rev = {}
        updated_ds_id_and_rev['_id'] = write_tuple_1[0]
        updated_ds_id_and_rev['_rev'] = write_tuple_1[1]

        # deleting attachment from the previous (wrong) revision raises document update conflict
        #with self.assertRaises(Exception):
        #    self.ds.delete_attachment(doc=updated_ds_id_and_rev, attachment_name=attachment_name)

        # operations on previous versions are not allowed
        #with self.assertRaises(Exception):
        #    self.ds.create_attachment(doc=updated_ds_id_and_rev, data=some_text,
        #        attachment_name=attachment_name, content_type=None,
        #        datastore_name="")

        # send in an incorrect document _id
        with self.assertRaises(NotFound):
            self.ds.create_attachment(doc="incorrect_id", data=data,
                attachment_name=attachment_name, content_type=None,
                datastore_name="")

        # send in an incorrect document _id
        with self.assertRaises(NotFound):
            self.ds.read_attachment(doc="incorrect_id", attachment_name=attachment_name,
                datastore_name="")

        # send in an incorrect attachment_name
        with self.assertRaises(NotFound):
            self.ds.read_attachment(doc=ds_id_and_rev['_id'],
                attachment_name="incorrect_attachment", datastore_name="")

        # send in an incorrect document_id
        with self.assertRaises(NotFound):
            self.ds.update_attachment(doc="incorrect_id", attachment_name=attachment_name,
                data=some_text)

        # send in an incorrect attachment_name; this should work because update creates an
        # attachment when it can't find an attachment to update
        self.ds.update_attachment(ds_id_and_rev['_id'], attachment_name="incorrect_attachment",
            data=some_text)

        # send in an incorrect attachment_name; interestingly, this is not an error
        # This is an error in couchbase
        #self.ds.delete_attachment(doc=ds_id_and_rev['_id'], attachment_name='no_such_file')

        # send in an incorrect document_id
        with self.assertRaises(NotFound):
            self.ds.delete_attachment(doc="incorrect_id", attachment_name='no_such_file')


    #@skip("DONT SKIP THIS TEST")
    def test_views(self):

        self.ds._update_views()

        # HACK: Both Predicates so that this test works
        from pyon.ion.resource import Predicates
        Predicates[OWNER_OF] = dict(domain=[RT.ActorIdentity], range=[RT.InstrumentDevice, RT.Dataset])
        Predicates[HAS_A] = dict(domain=[RT.Resource], range=[RT.Resource])
        Predicates[BASED_ON] = dict(domain=[RT.Dataset], range=[RT.Dataset])

        admin_user_id = self._create_resource(RT.ActorIdentity, 'John Doe', description='Marine Operator', lcstate=LCS.DEPLOYED_AVAILABLE)

        admin_profile_id = self._create_resource(RT.UserInfo, 'J.D. Profile', description='Some User',
            contact=IonObject('ContactInformation', **{"individual_names_given": "John Doe",
                                                       "email": "johnny@iamdevops.com"}))

        other_user_id = self._create_resource(RT.ActorIdentity, 'Paul Smithy', description='Other user')

        plat1_obj_id = self._create_resource(RT.PlatformDevice, 'Buoy1', description='My Platform')

        inst1_obj_id = self._create_resource(RT.InstrumentDevice, 'CTD1', description='My Instrument')

        inst2_obj_id = self._create_resource(RT.InstrumentDevice, 'CTD2', description='Other Instrument')

        ds1_obj_id = self._create_resource(RT.Dataset, 'DS_CTD_L0', description='My Dataset CTD L0', lcstate=LCS.DEPLOYED_AVAILABLE)

        ds2_obj_id = self._create_resource(RT.Dataset, 'DS_CTD_L1', description='My Dataset CTD L1')

        aid1, _ = self.ds.create_association(admin_user_id, OWNER_OF, inst1_obj_id)

        asso_id = self.ds.create_association(admin_user_id, HAS_A, admin_profile_id)[0]

        self.ds.create_association(admin_user_id, OWNER_OF, ds1_obj_id)

        self.ds.create_association(other_user_id, OWNER_OF, inst2_obj_id)

        self.ds.create_association(plat1_obj_id, HAS_A, inst1_obj_id)

        self.ds.create_association(inst1_obj_id, HAS_A, ds1_obj_id)

        self.ds.create_association(ds1_obj_id, BASED_ON, ds1_obj_id)

        with self.assertRaises(BadRequest) as cm:
            self.ds.create_association(ds1_obj_id, BASED_ON, ds1_obj_id)
        self.assertTrue(cm.exception.message.startswith("Association between"))

        # Subject -> Object direction
        obj_ids1, obj_assocs1 = self.ds.find_objects(admin_user_id, id_only=True)
        self.assertEquals(len(obj_ids1), 3)
        self.assertEquals(len(obj_assocs1), 3)
        self.assertEquals(set(obj_ids1), set([inst1_obj_id, ds1_obj_id, admin_profile_id]))

        obj_ids1n, obj_assocs1n = self.ds.find_objects("Non_Existent", id_only=True)
        self.assertEquals(len(obj_ids1n), 0)
        self.assertEquals(len(obj_assocs1n), 0)

        obj_ids1a, obj_assocs1a = self.ds.find_objects(admin_user_id, id_only=False)
        self.assertEquals(len(obj_ids1a), 3)
        self.assertEquals(len(obj_assocs1a), 3)
        self.assertEquals(set([o._id for o in obj_ids1a]), set([inst1_obj_id, ds1_obj_id, admin_profile_id]))
        self.assertEquals(set([type(o).__name__ for o in obj_ids1a]), set([RT.UserInfo, RT.InstrumentDevice, RT.Dataset]))

        obj_ids1an, obj_assocs1an = self.ds.find_objects("Non_Existent", id_only=False)
        self.assertEquals(len(obj_ids1an), 0)
        self.assertEquals(len(obj_assocs1an), 0)

        obj_ids2, obj_assocs2 = self.ds.find_objects(admin_user_id, OWNER_OF, id_only=True)
        self.assertEquals(len(obj_ids2), 2)
        self.assertEquals(len(obj_assocs2), 2)
        self.assertEquals(set(obj_ids2), set([inst1_obj_id, ds1_obj_id]))

        obj_ids3, _ = self.ds.find_objects(admin_user_id, OWNER_OF, RT.InstrumentDevice, id_only=True)
        self.assertEquals(len(obj_ids3), 1)
        self.assertEquals(obj_ids3[0], inst1_obj_id)


        # Object -> Subject direction
        sub_ids1, sub_assoc1 = self.ds.find_subjects(None, None, inst1_obj_id, id_only=True)
        self.assertEquals(len(sub_ids1), 2)
        self.assertEquals(len(sub_assoc1), 2)
        self.assertEquals(set(sub_ids1), set([admin_user_id, plat1_obj_id]))

        sub_ids1a, sub_assoc1a = self.ds.find_subjects(None, None, inst1_obj_id, id_only=False)
        self.assertEquals(len(sub_ids1a), 2)
        self.assertEquals(len(sub_assoc1a), 2)
        self.assertEquals(set([o._id for o in sub_ids1a]), set([admin_user_id, plat1_obj_id]))

        sub_ids1an, sub_assoc1an = self.ds.find_subjects(None, None, "Non_Existent", id_only=False)
        self.assertEquals(len(sub_ids1an), 0)
        self.assertEquals(len(sub_assoc1an), 0)

        sub_ids2, sub_assoc2 = self.ds.find_subjects(None, OWNER_OF, inst1_obj_id, id_only=True)
        self.assertEquals(len(sub_ids2), 1)
        self.assertEquals(len(sub_assoc2), 1)
        self.assertEquals(set(sub_ids2), set([admin_user_id]))

        sub_ids3, _ = self.ds.find_subjects(RT.ActorIdentity, OWNER_OF, inst1_obj_id, id_only=True)
        self.assertEquals(len(sub_ids3), 1)
        self.assertEquals(set(sub_ids3), set([admin_user_id]))

        self.ds._update_views()

        # Find all resources
        res_ids1, res_assoc1 = self.ds.find_res_by_type(None, None, id_only=True)
        self.assertEquals(len(res_ids1), 8)
        self.assertEquals(len(res_assoc1), 8)

        # Find resources by type
        res_ids1, res_assoc1 = self.ds.find_res_by_type(RT.ActorIdentity, id_only=True)
        self.assertEquals(len(res_ids1), 2)
        self.assertEquals(len(res_assoc1), 2)
        self.assertEquals(set(res_ids1), set([admin_user_id, other_user_id]))

        res_ids1a, res_assoc1a = self.ds.find_res_by_type(RT.ActorIdentity, id_only=False)
        self.assertEquals(len(res_ids1a), 2)
        self.assertEquals(len(res_assoc1a), 2)
        self.assertEquals(set([o._id for o in res_ids1a]), set([admin_user_id, other_user_id]))
        #self.assertEquals(set([o['_id'] for o in res_ids1a]), set([admin_user_id, other_user_id]))
        self.assertEquals(set([o.lcstate for o in res_ids1a]), set([LCS.DRAFT_PRIVATE, LCS.DEPLOYED_AVAILABLE]))

        res_ids2, res_assoc2 = self.ds.find_res_by_type(RT.ActorIdentity, LCS.DEPLOYED_AVAILABLE, id_only=True)
        self.assertEquals(len(res_ids2), 1)
        self.assertEquals(len(res_assoc2), 1)
        self.assertEquals(set(res_ids2), set([admin_user_id]))

        #TODO TRY THIS ON COUCHBASE
        ##res_ids2n, res_assoc2n = self.ds.find_res_by_name("NONE##", "XXXXX", id_only=True)
        res_ids2n, res_assoc2n = self.ds.find_res_by_type("NONE11", LCS.DEPLOYED_AVAILABLE, id_only=True)
        #res_ids2n, res_assoc2n = self.ds.find_res_by_type("NONE11", LCS.DEPLOYED_AVAILABLE, id_only=True)
        self.assertEquals(len(res_ids2n), 0)
        self.assertEquals(len(res_assoc2n), 0)

        # Find resources by lcstate
        res_ids1, res_assoc1 = self.ds.find_res_by_lcstate(LCS.DEPLOYED_AVAILABLE, id_only=True)
        self.assertEquals(len(res_ids1), 2)
        self.assertEquals(len(res_assoc1), 2)
        self.assertEquals(set(res_ids1), set([admin_user_id, ds1_obj_id]))

        res_ids1a, res_assoc1a = self.ds.find_res_by_lcstate(LCS.DEPLOYED_AVAILABLE, id_only=False)
        self.assertEquals(len(res_ids1a), 2)
        self.assertEquals(len(res_assoc1a), 2)
        self.assertEquals(set([o._id for o in res_ids1a]), set([admin_user_id, ds1_obj_id]))
        self.assertEquals(set([type(o).__name__ for o in res_ids1a]), set([RT.ActorIdentity, RT.Dataset]))

        res_ids2, res_assoc2 = self.ds.find_res_by_lcstate( LCS.DEPLOYED_AVAILABLE, RT.ActorIdentity, id_only=True)
        self.assertEquals(len(res_ids2), 1)
        self.assertEquals(len(res_assoc2), 1)
        self.assertEquals(set(res_ids2), set([admin_user_id]))

        #TODO
        ##res_ids2n, res_assoc2n = self.ds.find_res_by_type("NONE##", "XXXXX", id_only=True)
        res_ids2n, res_assoc2n = self.ds.find_res_by_type("NONE11", "XXXXX", id_only=True)
        self.assertEquals(len(res_ids2n), 0)
        self.assertEquals(len(res_assoc2n), 0)

        # Find resources by lcstate - hierarchical
        res_ids1, res_assoc1 = self.ds.find_res_by_lcstate(LCS.AVAILABLE, id_only=True)
        self.assertEquals(len(res_ids1), 2)
        self.assertEquals(len(res_assoc1), 2)
        self.assertEquals(set(res_ids1), set([admin_user_id, ds1_obj_id]))

        res_ids1, res_assoc1 = self.ds.find_res_by_lcstate(LCS.REGISTERED, id_only=True)
        self.assertEquals(len(res_ids1), 2)
        self.assertEquals(len(res_assoc1), 2)
        self.assertEquals(set(res_ids1), set([admin_user_id, ds1_obj_id]))

        res_ids1, res_assoc1 = self.ds.find_res_by_lcstate(LCS.PRIVATE, id_only=True)
        self.assertEquals(len(res_ids1), 6)
        self.assertEquals(len(res_assoc1), 6)

        # Find resources by name
        res_ids1, res_assoc1 = self.ds.find_res_by_name('CTD1', id_only=True)
        self.assertEquals(len(res_ids1), 1)
        self.assertEquals(len(res_assoc1), 1)
        self.assertEquals(set(res_ids1), set([inst1_obj_id]))

        res_ids1a, res_assoc1a = self.ds.find_res_by_name('CTD2', id_only=False)
        self.assertEquals(len(res_ids1a), 1)
        self.assertEquals(len(res_assoc1a), 1)
        self.assertEquals(set([o._id for o in res_ids1a]), set([inst2_obj_id]))
        self.assertEquals(set([type(o).__name__ for o in res_ids1a]), set([RT.InstrumentDevice]))

        res_ids2, res_assoc2 = self.ds.find_res_by_name( 'John Doe', RT.ActorIdentity, id_only=True)
        self.assertEquals(len(res_ids2), 1)
        self.assertEquals(len(res_assoc2), 1)
        self.assertEquals(set(res_ids2), set([admin_user_id]))

        res_ids2n, res_assoc2n = self.ds.find_res_by_name("NONE11", "XXXXX", id_only=True)
        #TODO try this with couchbase client
        #res_ids2n, res_assoc2n = self.ds.find_res_by_name("NONE##", "XXXXX", id_only=True)
        self.assertEquals(len(res_ids2n), 0)
        self.assertEquals(len(res_assoc2n), 0)

        # Find associations by triple
        assocs = self.ds.find_associations(admin_user_id, OWNER_OF, inst1_obj_id, id_only=True)
        self.assertEquals(len(assocs), 1)
        self.assertEquals(assocs[0], aid1)

        assocs = self.ds.find_associations(admin_user_id, OWNER_OF, inst1_obj_id, id_only=False)
        self.assertEquals(len(assocs), 1)
        self.assertEquals(type(assocs[0]).__name__, "Association")

        assocs = self.ds.find_associations(admin_user_id, None, inst1_obj_id, id_only=True)
        self.assertEquals(len(assocs), 1)
        self.assertEquals(assocs[0], aid1)

        assocs = self.ds.find_associations(subject=inst1_obj_id, id_only=True)
        self.assertEquals(len(assocs), 1)

        assocs = self.ds.find_associations(obj=inst1_obj_id, id_only=True)
        self.assertEquals(len(assocs), 2)

        assocs = self.ds.find_associations(None, OWNER_OF, None, id_only=True)
        self.assertEquals(len(assocs), 3)

        assocs = self.ds.find_associations(anyside=inst1_obj_id, id_only=True)
        self.assertEquals(len(assocs), 3)

        assocs = self.ds.find_associations(anyside=inst1_obj_id, predicate=HAS_A, id_only=True)
        self.assertEquals(len(assocs), 2)

        assocs = self.ds.find_associations(anyside=[inst1_obj_id,other_user_id], id_only=True)
        self.assertEquals(len(assocs), 4)

        assocs = self.ds.find_associations(anyside=[[inst1_obj_id, HAS_A], [other_user_id, OWNER_OF]], id_only=True)
        self.assertEquals(len(assocs), 3)

        assocs = self.ds.find_associations(anyside=[(inst1_obj_id, HAS_A), (other_user_id, OWNER_OF)], id_only=True)
        self.assertEquals(len(assocs), 3)


        view_res = self.ds.find_by_view('association', 'by_id', id_only=True, convert_doc=False)
        self.assertEquals(len(view_res), 14)

        view_res = self.ds.find_by_view('association', 'by_id', id_only=False, convert_doc=False)
        self.assertEquals(len(view_res), 14)

        view_res = self.ds.find_by_view('resource', 'by_name', id_only=True, convert_doc=True)
        self.assertEquals(len(view_res), 8)

        ## Todo:  Need to add into directory service and check this
        view_res = self.ds.find_by_view('directory', 'by_parent', id_only=True, convert_doc=True)
        self.assertEquals(len(view_res), 0)

        view_res = self.ds.find_by_view('resource', 'by_name', id_only=True, convert_doc=True)
        self.assertEquals(len(view_res), 8)

        view_res = self.ds.find_by_view('resource', 'by_name', id_only=False, convert_doc=True)
        self.assertEquals(len(view_res), 8)
        view_res = self.ds.find_by_view('resource', 'by_name', id_only=False, convert_doc=False)
        self.assertEquals(len(view_res), 8)

        view_res = self.ds.find_by_view('association', 'by_id', id_only=False, convert_doc=False)
        self.assertEquals(len(view_res), 14)



    #@skip ("don't skip this test")
    def test_read_and_create(self, is_persistent= True):

        # Create should throw exception the second time
        with self.assertRaises(BadRequest):
            self.ds.create_datastore()

        # Call ops with wrong object type and make sure exception is thrown
        with self.assertRaises(BadRequest):
            self.ds.create({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.create_mult([{"foo": "bar"}])

        with self.assertRaises(BadRequest):
            self.ds.read({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.read_mult([{"foo": "bar"}])

        with self.assertRaises(BadRequest):
            self.ds.update({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.delete({"foo": "bar"})

        # Should see new data
        self.assertIn(self.datastore_name, self.ds.list_datastores())


        # Something should be returned
        self.assertTrue(self.ds.info_datastore() is not None)

        ## Todo
        res = self.ds.list_objects()
        numcoredocs = len(res)
        if is_persistent:
            self.assertTrue(numcoredocs >= 0)
            ##self.assertTrue(numcoredocs > 1)
            self.ds._update_views()

        # Construct user role objects
        admin_role = {
            "name":"Admin",
            "description":"Super user"
        }


        admin_role_obj = IonObject('UserRole', admin_role)
        admin_role_tuple = self.ds.create(admin_role_obj)
        self.assertTrue(len(admin_role_tuple) == 2)

        admin_role_ooi_id = admin_role_tuple[0]

        data_provider_role = {
            "name":"Data Provider",
            "description":"User allowed to ingest data sets"
        }
        data_provider_role_obj = IonObject('UserRole', data_provider_role)
        data_provider_role_tuple = self.ds.create(data_provider_role_obj)
        self.assertTrue(len(data_provider_role_tuple) == 2)

        data_provider_role_ooi_id = data_provider_role_tuple[0]

        marine_operator_role = {
            "name":"Marine Operator",
            "description":"User allowed to administer instruments"
        }
        marine_operator_role_obj = IonObject('UserRole', marine_operator_role)
        marine_operator_role_tuple = self.ds.create(marine_operator_role_obj)
        self.assertTrue(len(marine_operator_role_tuple) == 2)

        marine_operator_role_ooi_id = marine_operator_role_tuple[0]

        role_objs = self.ds.read_mult([admin_role_ooi_id, data_provider_role_ooi_id, marine_operator_role_ooi_id])

        self.assertTrue(len(role_objs) == 3)
        self.assertTrue(role_objs[0]._id == admin_role_ooi_id)
        self.assertTrue(role_objs[1]._id == data_provider_role_ooi_id)
        self.assertTrue(role_objs[2]._id == marine_operator_role_ooi_id)

        # Construct three user info objects and assign them roles
        hvl_contact_info = {
            "individual_names_given": "Heitor Villa-Lobos",
            "email": "prelude1@heitor.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Legendary Brazilian composer"}
            ]
        }
        hvl_contact_info_obj = IonObject('ContactInformation', hvl_contact_info)
        hvl_user_info = {
            "name": "Heitor Villa-Lobos",
            "contact": hvl_contact_info_obj
        }
        hvl_user_info_obj = IonObject('UserInfo', hvl_user_info)
        hvl_user_info_tuple = self.ds.create(hvl_user_info_obj)
        self.assertTrue(len(hvl_user_info_tuple) == 2)

        heitor_villa_lobos_ooi_id = hvl_user_info_tuple[0]

        ats_contact_info = {
            "individual_names_given": "Andres Torres Segovia",
            "email": "asturas@andres.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Legendary Concert Guitarist"}
            ]
        }
        ats_contact_info_obj = IonObject('ContactInformation', ats_contact_info)
        ats_user_info = {
            "name": "Andres Torres Segovia",
            "contact": ats_contact_info_obj
        }
        ats_user_info_obj = IonObject('UserInfo', ats_user_info)
        ats_user_info_tuple = self.ds.create(ats_user_info_obj)
        self.assertTrue(len(ats_user_info_tuple) == 2)

        pok_contact_info = {
            "individual_names_given": "Per-Olov Kindgren",
            "email": "etude6@per.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Composer and YouTube star"}
            ]
        }
        pok_contact_info_obj = IonObject('ContactInformation', pok_contact_info)
        pok_user_info = {
            "name": "Per-Olov Kindgren",
            "contact": pok_contact_info_obj
        }
        pok_user_info_obj = IonObject('UserInfo', pok_user_info)
        pok_user_info_tuple = self.ds.create(pok_user_info_obj)
        self.assertTrue(len(pok_user_info_tuple) == 2)

        # List all objects in data store and confirm there are six docs
        res = self.ds.list_objects()
        # There are indices. Therefore can't could all docs
        self.assertTrue(len(res) == 6 + numcoredocs)


        # Create an Ion object with default values set (if any)
        data_set = IonObject('Dataset')
        self.assertTrue(isinstance(data_set, interface.objects.Dataset))

        # Assign values to object fields
        data_set.description = "Real-time water data for Choptank River near Greensboro, MD"
        #data_set.min_datetime = "2011-08-04T13:15:00Z"
        #data_set.max_datetime = "2011-08-09T19:15:00Z"
        #data_set.variables = [
        #        {"name":"water_height", "value":"ft"}
        #]

        # Write Dataset object"
        write_tuple_1 = self.ds.create(data_set)
        self.assertTrue(len(write_tuple_1) == 2)

        # Save off the object UUID
        data_set_uuid = write_tuple_1[0]

        # Read back the HEAD version of the object and validate fields
        data_set_read_obj = self.ds.read(data_set_uuid)
        self.assertTrue(data_set_read_obj._id == data_set_uuid)
        self.assertTrue(isinstance(data_set_read_obj, interface.objects.Dataset))
        self.assertTrue(data_set_read_obj.description == "Real-time water data for Choptank River near Greensboro, MD")
        self.assertTrue('type_' in data_set_read_obj)

        # Update Dataset's Description field and write
        data_set_read_obj.description = "Updated Description"
        write_tuple_2 = self.ds.update(data_set_read_obj)
        self.assertTrue(len(write_tuple_2) == 2)

        # Retrieve the updated Dataset
        data_set_read_obj_2 = self.ds.read(data_set_uuid)
        self.assertTrue(data_set_read_obj_2._id == data_set_uuid)
        self.assertTrue(data_set_read_obj_2.description == "Updated Description")

        # Delete data store to clean up
        self.ds.delete_datastore()

        # Assert data store is now gone
        self.assertNotIn(database_name, self.ds.list_datastores())


    '''
    def test_prf (self):
        self.ds = CouchbaseDataStore()
        ds, ds_name = self.ds._get_datastore(datastore_name="default")
        self.assertIsInstance(ds, Bucket)

        timer = IonObject("IntervalTimer", {"start_time": "111", "interval": 3, "end_time": "0"})

        start = time()
        for x in range(0, 3000):
            # Create
            id, rev = self.ds.create(timer)

            # Read and verify create
            obj = self.ds.read(id)
            self.assertTrue(type(obj)==type(timer), "Types don't match %s : %s" %(type(obj), type(timer)))
            self.assertEqual(obj.start_time, timer.start_time)

            # Update
            updated_data = "2222"
            obj.start_time = updated_data
            id2 , rev2 = self.ds.update(obj)

            # Verify update
            self.assertEqual(id, id2)
            obj2 = self.ds.read(id2)
            self.assertEqual(obj2.start_time, updated_data)

            # Update not-existing object
            temp = IonObject("IntervalTimer", {"start_time": "111", "interval": 3, "end_time": "0"})
            temp._id = "233"
            with self.assertRaises(NotFound):
                self.ds.update(temp)


            # Delete
            #self.ds.delete(obj)
            # Verify delete
            #with self.assertRaises(NotFound):
            #    self.ds.delete(obj)

        end = time()
        diff = end - start
        f = open('test_out', 'w')
        f.write(str(diff))
        f.close()

        with self.assertRaises(NotFound):
            self.ds.delete(obj2)
        with self.assertRaises(NotFound):
            self.ds.read(id)
        # Delete

        #self.assertTrue(hasattr(obj[2], "start_time"))



        #ds = self.ds.create_datastore(datastore_name="testik9")
        #self.ds.delete_datastore("testing33333")

        #print "\n\n\n ###", self.ds.list_datastores()
        '''




'''
@attr('seman2', group='datastore')
class TestCouchdb(IonIntegrationTestCase):

    def setUp(self):
        log.debug("cfg %s", repr(CFG['server'].keys()))
        self.hostname = CFG['server']['couchdb']['host']
        self.port = CFG['server']['couchdb']['port']
        self.resources = {}
        self.datastore_name = database_name
        self.ds = CouchDB_DataStore(datastore_name=self.datastore_name, profile=DataStore.DS_PROFILE.RESOURCES)

    def _create_resource(self, restype, name, *args, **kwargs):
        res_obj = IonObject(restype, dict(name=name, **kwargs))
        res_obj_res = self.ds.create(res_obj)
        res_obj._id = res_obj_res[0]
        self.resources[name] = res_obj
        return res_obj_res[0]

    def test_connection(self):
        self._do_test(self.ds)

        # start fresh
        try:
            self.ds.delete_datastore()
        except NotFound:
            pass

        self.ds.create_datastore()
        ds, ds_name = self.ds._get_datastore()
        #self.assertIsInstance(ds, Bucket)

        timer = IonObject("IntervalTimer", {"start_time": "111", "interval": 3, "end_time": "0"})

        # Create
        id, rev = self.ds.create(timer)

        # Read and verify create
        obj = self.ds.read(id)
        self.assertTrue(type(obj)==type(timer), "Types don't match %s : %s" %(type(obj), type(timer)))
        self.assertEqual(obj.start_time, timer.start_time)



        dbs = self.ds.list_datastores()
        # Views
        res = self.ds.list_objects()
        numcoredocs = len(res)
        self.ds._update_views()


        # HACK: Both Predicates so that this test works
        from pyon.ion.resource import Predicates
        Predicates[OWNER_OF] = dict(domain=[RT.ActorIdentity], range=[RT.InstrumentDevice, RT.Dataset])
        Predicates[HAS_A] = dict(domain=[RT.Resource], range=[RT.Resource])
        Predicates[BASED_ON] = dict(domain=[RT.Dataset], range=[RT.Dataset])

        # association
        user_id = self._create_resource(RT.ActorIdentity, 'John Doe', description='Marine Operator', lcstate=LCS.DEPLOYED_AVAILABLE)
        profile_id = self._create_resource(RT.UserInfo, 'J.D. Profile', description='Some User',
            contact=IonObject('ContactInformation', **{"individual_names_given": "John Doe",
                                                       "email": "johnny@iamdevops.com"}))

        inst_id = self._create_resource(RT.InstrumentDevice, 'CTD1', description='My Instrument')
        plat_obj_id = self._create_resource(RT.PlatformDevice, 'Buoy1', description='My Platform')

        #aid1, _ = self.ds.create_association(user_id, OWNER_OF, inst_id)
        self.ds.find_associations(plat_obj_id, HAS_A, inst_id)
        self.ds.create_association(plat_obj_id, HAS_A, inst_id)
        assocs = self.ds.find_associations(user_id, OWNER_OF, inst_id, id_only=True)
        self.assertEquals(len(assocs), 1)
        #self.assertEquals(assocs[0], aid1)




    def _do_test(self, is_persistent=True):
        self.resources = {}
        # Just in case previous run failed without cleaning up,
        # delete data store
        try:
            self.ds.delete_datastore()
        except NotFound:
            pass
            # Create should succeed and not throw error
        self.ds.create_datastore()

        # Create should throw exception the second time
        with self.assertRaises(BadRequest):
            self.ds.create_datastore()

        # Call ops with wrong object type and make sure exception is thrown
        with self.assertRaises(BadRequest):
            self.ds.create({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.create_mult([{"foo": "bar"}])

        with self.assertRaises(BadRequest):
            self.ds.read({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.read_mult([{"foo": "bar"}])

        with self.assertRaises(BadRequest):
            self.ds.update({"foo": "bar"})

        with self.assertRaises(BadRequest):
            self.ds.delete({"foo": "bar"})

        # Should see new data
        self.assertIn(self.datastore_name, self.ds.list_datastores())


        # Something should be returned
        self.assertTrue(self.ds.info_datastore() is not None)

        res = self.ds.list_objects()
        numcoredocs = len(res)

        if is_persistent:
            self.assertTrue(numcoredocs > 1)
            self.ds._update_views()

        # Construct user role objects
        admin_role = {
            "name":"Admin",
            "description":"Super user"
        }
        admin_role_obj = IonObject('UserRole', admin_role)
        admin_role_tuple = self.ds.create(admin_role_obj)
        self.assertTrue(len(admin_role_tuple) == 2)

        admin_role_ooi_id = admin_role_tuple[0]

        data_provider_role = {
            "name":"Data Provider",
            "description":"User allowed to ingest data sets"
        }
        data_provider_role_obj = IonObject('UserRole', data_provider_role)
        data_provider_role_tuple = self.ds.create(data_provider_role_obj)
        self.assertTrue(len(data_provider_role_tuple) == 2)

        data_provider_role_ooi_id = data_provider_role_tuple[0]

        marine_operator_role = {
            "name":"Marine Operator",
            "description":"User allowed to administer instruments"
        }
        marine_operator_role_obj = IonObject('UserRole', marine_operator_role)
        marine_operator_role_tuple = self.ds.create(marine_operator_role_obj)
        self.assertTrue(len(marine_operator_role_tuple) == 2)

        marine_operator_role_ooi_id = marine_operator_role_tuple[0]

        role_objs = self.ds.read_mult([admin_role_ooi_id, data_provider_role_ooi_id, marine_operator_role_ooi_id])

        self.assertTrue(len(role_objs) == 3)
        self.assertTrue(role_objs[0]._id == admin_role_ooi_id)
        self.assertTrue(role_objs[1]._id == data_provider_role_ooi_id)
        self.assertTrue(role_objs[2]._id == marine_operator_role_ooi_id)

        # Construct three user info objects and assign them roles
        hvl_contact_info = {
            "individual_names_given": "Heitor Villa-Lobos",
            "email": "prelude1@heitor.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Legendary Brazilian composer"}
            ]
        }
        hvl_contact_info_obj = IonObject('ContactInformation', hvl_contact_info)
        hvl_user_info = {
            "name": "Heitor Villa-Lobos",
            "contact": hvl_contact_info_obj
        }
        hvl_user_info_obj = IonObject('UserInfo', hvl_user_info)
        hvl_user_info_tuple = self.ds.create(hvl_user_info_obj)
        self.assertTrue(len(hvl_user_info_tuple) == 2)

        heitor_villa_lobos_ooi_id = hvl_user_info_tuple[0]

        ats_contact_info = {
            "individual_names_given": "Andres Torres Segovia",
            "email": "asturas@andres.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Legendary Concert Guitarist"}
            ]
        }
        ats_contact_info_obj = IonObject('ContactInformation', ats_contact_info)
        ats_user_info = {
            "name": "Andres Torres Segovia",
            "contact": ats_contact_info_obj
        }
        ats_user_info_obj = IonObject('UserInfo', ats_user_info)
        ats_user_info_tuple = self.ds.create(ats_user_info_obj)
        self.assertTrue(len(ats_user_info_tuple) == 2)

        pok_contact_info = {
            "individual_names_given": "Per-Olov Kindgren",
            "email": "etude6@per.com",
            "variables": [
                {"name": "Claim To Fame", "value": "Composer and YouTube star"}
            ]
        }
        pok_contact_info_obj = IonObject('ContactInformation', pok_contact_info)
        pok_user_info = {
            "name": "Per-Olov Kindgren",
            "contact": pok_contact_info_obj
        }
        pok_user_info_obj = IonObject('UserInfo', pok_user_info)
        pok_user_info_tuple = self.ds.create(pok_user_info_obj)
        self.assertTrue(len(pok_user_info_tuple) == 2)

        # List all objects in data store and confirm there are six docs
        res = self.ds.list_objects()
        # There are indices. Therefore can't could all docs
        self.assertTrue(len(res) == 6 + numcoredocs)

        # Create an Ion object with default values set (if any)
        data_set = IonObject('Dataset')
        self.assertTrue(isinstance(data_set, interface.objects.Dataset))

        # Assign values to object fields
        data_set.description = "Real-time water data for Choptank River near Greensboro, MD"
        #data_set.min_datetime = "2011-08-04T13:15:00Z"
        #data_set.max_datetime = "2011-08-09T19:15:00Z"
        #data_set.variables = [
        #        {"name":"water_height", "value":"ft"}
        #]

        # Write Dataset object"
        write_tuple_1 = self.ds.create(data_set)
        self.assertTrue(len(write_tuple_1) == 2)

        # Save off the object UUID
        data_set_uuid = write_tuple_1[0]

        # Read back the HEAD version of the object and validate fields
        data_set_read_obj = self.ds.read(data_set_uuid)
        self.assertTrue(data_set_read_obj._id == data_set_uuid)
        self.assertTrue(isinstance(data_set_read_obj, interface.objects.Dataset))
        self.assertTrue(data_set_read_obj.description == "Real-time water data for Choptank River near Greensboro, MD")
        self.assertTrue('type_' in data_set_read_obj)

        # Update Dataset's Description field and write
        data_set_read_obj.description = "Updated Description"
        write_tuple_2 = self.ds.update(data_set_read_obj)
        self.assertTrue(len(write_tuple_2) == 2)

        # Retrieve the updated Dataset
        data_set_read_obj_2 = self.ds.read(data_set_uuid)
        self.assertTrue(data_set_read_obj_2._id == data_set_uuid)
        self.assertTrue(data_set_read_obj_2.description == "Updated Description")

        # List all the revisions of Dataset in data store, should be two
        res = self.ds.list_object_revisions(data_set_uuid)
        self.assertTrue(len(res) == 2)

        # Do another update to the object
        data_set_read_obj_2.description = "USGS instantaneous value data for station 01491000"
        write_tuple_3 = self.ds.update(data_set_read_obj_2)

        # List revisions of Dataset in data store, should now be three
        res = self.ds.list_object_revisions(data_set_uuid)
        self.assertTrue(len(res) == 3)

        # Retrieve original version of Dataset
        obj1 = self.ds.read(data_set_uuid, rev_id=write_tuple_1[1])
        self.assertTrue(obj1._id == data_set_uuid)
        self.assertTrue(obj1.description == "Real-time water data for Choptank River near Greensboro, MD")

        # Retrieve second version of Dataset
        obj2 = self.ds.read(data_set_uuid, rev_id=write_tuple_2[1])
        self.assertTrue(obj2._id == data_set_uuid)
        self.assertTrue(obj2.description == "Updated Description")

        # Retrieve third version of Dataset
        obj3 = self.ds.read(data_set_uuid, rev_id=write_tuple_3[1])
        self.assertTrue(obj3._id == data_set_uuid)
        self.assertTrue(obj3.description == "USGS instantaneous value data for station 01491000")

        # Retrieve HEAD version of Dataset
        head = self.ds.read(data_set_uuid)
        self.assertTrue(head._id == data_set_uuid)
        self.assertTrue(head.description == "USGS instantaneous value data for station 01491000")

        # Delete Dataset by object id
        self.ds.delete(head)

        # Try to re-delete Dataset by object id.  Should throw exception.
        with self.assertRaises(NotFound):
            self.ds.delete(head._id)

        # List all objects in data store, should be back to six
        res = self.ds.list_objects()
        self.assertTrue(len(res) == 6 + numcoredocs)

        # List revisions of now deleted Dataset, should be empty list
        res = self.ds.list_object_revisions(data_set_uuid)
        self.assertTrue(len(res) == 0)

        o1 = IonObject("Dataset", name="One more")
        o2 = IonObject("Dataset", name="Another one")
        res = self.ds.create_mult((o1, o2))
        self.assertTrue(all([success for success, oid, rev in res]))

        res = self.ds.list_objects()
        self.assertTrue(len(res) == 8 + numcoredocs)

        # Delete data store to clean up
        self.ds.delete_datastore()

        # Assert data store is now gone
        self.assertNotIn(self.datastore_name, self.ds.list_datastores())
'''
