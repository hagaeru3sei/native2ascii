import Vue from 'vue/dist/vue.js'
import axios from 'axios'
import downloadjs from 'downloadjs'
import Vuetable from 'vuetable-2/src/components/Vuetable.vue'
Vue.use(Vuetable);

const msg = "Convert native2ascii for java apps";
const languageEndpoint = 'http://localhost:8800/lang';
const endpoint = 'http://localhost:8800/api';


function getLanguageCodes() {
  let languages = [];
  axios.get(languageEndpoint).then(res => {
    console.log(res);
    languages = res.data.languages
  });
  console.log(languages);
  return languages;
}


// attach message
new Vue({
  data : {
    message: msg
  }
}).$mount('#message');


// Set languages
const formApp = new Vue({
  el: '#newRecordForm',
  data: {
    /**
     * example:
     *   ['en', 'jp']
     */
    languages: [],

    /**
     * example:
     *   {
     *     'en': {
     *       'key': '',
     *       'value': '',
     *       'description': ''
     *     },,,
     *   }
     */
    jsonRequest : {}
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  computed: {
    keyName: function (name, lang) {
      return name + "_" + lang
    }
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log(res);
        this.languages = res.data.languages
      });
    },
    addNewRecord: function () {
      console.log("Called addNewRecord.");
      console.log(this);
      let items = {};
      [].slice.call(Object.keys(this.jsonRequest)).forEach(lang => {
         let item = this.jsonRequest[lang];
         items[lang] = {
           key: item.key,
           value: item.value,
           description: item.description
         }
      });
      console.log("JSON string:", JSON.stringify(items));
      axios.post(endpoint, items).then(response => {
        console.log(response)
      });
      this.$emit('update.record', true)
    }
  }
});


// show list view
const viewApp = new Vue({
  el : '#listView',
  data : {
    items: []
  },
  mounted: function() {
    this.$nextTick(function () {
      console.log("ListView mounted.");
      this.get()
    })
  },
  updated: function () {
    this.$nextTick(function () {
      console.log("ListView updated.")
    })
  },
  methods: {
    get: function () {
      axios.get(endpoint).then(response => {
        console.log(endpoint, response);
        [].slice.call(response.data).forEach(element => {
          this.items.push(element)
        })
      });
    }
  }
});

// download
const downloadApp = new Vue({
  el: "#downloadForm",
  data: {
    selectedLanguage: 'en',
    languages: []
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log("GET /lang response", res);
        this.languages = res.data.languages
      });
    },
    download: function () {
      axios.get(endpoint + "/dl/" + this.selectedLanguage).then(response => {
        console.log("response:", response);
        downloadjs(response.data, 'message_' + this.selectedLanguage + '.properties')
      })
    }
  }
});

// upload property file
const uploadApp = new Vue({
  el : '#uploadForm',
  data: {
    selectedLanguage: 'en',
    languages: [],
    file: null
  },
  mounted: function() {
    this.$nextTick(function () {
      this.get()
    })
  },
  methods: {
    get: function() {
      axios.get(languageEndpoint).then(res => {
        console.log("GET /lang response", res);
        this.languages = res.data.languages
      });
    },
    selectedFile: function(event) {
      console.log("selectedFile");
      event.preventDefault();
      let files = event.target.files;
      this.file = files[0]
    },
    upload: function () {
      console.log("upload method called");
      let formData = new FormData();
      formData.append('upload_file', this.file);
      let config = {
        headers : {
          'content-type' : 'multipart/form-data'
        }
      };
      let url = endpoint + '/upload/' + this.selectedLanguage;
      axios.post(url, formData, config).then(res => {
        console.log("response", res)
      }).catch(e =>
        console.log("error", e)
      );
    }
  }
});

