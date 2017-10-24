import Vue from 'vue/dist/vue.js'
import axios from 'axios'
import Vuetable from 'vuetable-2/src/components/Vuetable.vue'
Vue.use(Vuetable);

const msg = "Convert native2ascii for java apps";
const languageEndpoint = 'http://localhost:8800/lang';
const endpoint = 'http://localhost:8800/api';

// attach message
new Vue({
  data : {
    message: msg
  }
}).$mount('#message');


// Set languages
new Vue({
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
      })
    }
  }
});


// show list view
new Vue({
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


