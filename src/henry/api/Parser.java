package henry.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.TypeAdapter;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import com.google.gson.stream.JsonWriter;

import java.io.IOException;

/**
 * Created by han on 6/16/14.
 */
public class Parser {
    private Gson gson;

    public Parser() {
        gson = new GsonBuilder()
                   .registerTypeAdapter(int.class, new CentAdaptor())
                   .excludeFieldsWithoutExposeAnnotation()
                   .create();
    }

    public <T> T parse(String json, Class<T> type) {
        return gson.fromJson(json, type);
    }

    static class CentAdaptor extends TypeAdapter<Integer> {
        @Override
        public void write(JsonWriter jsonWriter, Integer integer) throws IOException {

        }

        @Override
        public Integer read(JsonReader reader) throws IOException {
            if (reader.peek() == JsonToken.NULL) {
                reader.nextNull();
                return -1;
            }
            String val = reader.nextString();
            return getCentsFromString(val);
        }

        // Convertir precio en decimales en su equivalente en centavos.
        // Es decir "1.23" -> 123
        public static int getCentsFromString(String precio) {
            int dot = precio.indexOf('.');
            int decimalPlaces = 0;
            if (dot != -1) {
                decimalPlaces = precio.length() - dot - 1;
            }
            int digits = Integer.parseInt(precio.replaceAll("\\.", ""));
            while (decimalPlaces > 2) {
                digits /= 10;
                decimalPlaces--;
            }
            while (decimalPlaces < 2) {
                digits *= 10;
                decimalPlaces++;
            }
            return digits;
        }
    }
}
